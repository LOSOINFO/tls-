class Environment:
    def __init__(self, infrastructure_manager, nsprs_generator, nsprs_lifecycle_manager, failed_nspr_strategy, keep_information=True) -> None:
        # keep_information is used to decide wether to keep placements and matchings information for terminated VNFs (PS: keeping it may consume few more memory)
        self.infrastructure_manager = infrastructure_manager
        self.nsprs_generator = nsprs_generator
        self.nsprs_lifecycle_manager = nsprs_lifecycle_manager
        assert failed_nspr_strategy in [1,2]
        self.failed_nspr_strategy = failed_nspr_strategy
        self.keep_information = keep_information ; assert keep_information in [True,False]
        #--------------------
        self.cnodes_resources_upper_bounds = self.infrastructure_manager.get_resources_upper_bounds()
        #--------------------
        self.ongoing_nspr = None # the NSPR whose VNFs are being placed in current DRL iterations
        self.nspr_vnfs = None
        #--------------------
        self.id_of_vnf_to_place = None
        self.requirements_of_vnf_to_place = None
        #--------------------
        self.number_of_successful_nsprs_in_batch = 0

    def reset(self):
        # reset the slicing infrastructure
        self.infrastructure_manager.reset()
        # reset NSPRs generator
        self.nsprs_generator.reset()
        # reset NSPRs mifecycle manager
        self.nsprs_lifecycle_manager.reset()
        #-----------------------------------
        self.nsprs_lifecycle_manager.add_to_waiting_nsprs( self.nsprs_generator.generate() )
        self.load_a_nspr_from_current_batch_and_if_empty_receive_new_batch_of_nsprs_and_load_one()
        # describing infrastructure just after allow to take into account any changes that may occur in above function
        cnodes_description = self.infrastructure_manager.describe()
        self.number_of_successful_nsprs_in_batch = 0
        return [cnodes_description, self.requirements_of_vnf_to_place]

    def step(self, action):
        cnodes_description = None
        done = False
        info = ""
        #----------
        placed, reward = self.place(vnf_id=self.id_of_vnf_to_place, vnf_requirements=self.requirements_of_vnf_to_place, cnode_id=action+1) # action is in [0,n-1] while cnode_id should be in [1,n]
        if not placed:
            # restore already allocated resources
            self.infrastructure_manager.deallocate_whole_nspr(self.ongoing_nspr)
            if self.failed_nspr_strategy == 1: # add ongoing NSPR into delayed NSPRs (strategy 1)
                self.nsprs_lifecycle_manager.add_to_delayed_nsprs(self.ongoing_nspr)
            elif self.failed_nspr_strategy == 2: # add ongoing NSPR into NSPRs terminated after fail (strategy 2)
                if not self.keep_information:
                    # delete information about placement and matchings in NSPR
                    self.ongoing_nspr.unset_placements_and_matchings()
                self.nsprs_lifecycle_manager.add_to_terminated_nsprs_after_fail(self.ongoing_nspr)

            done = self.load_a_nspr_from_current_batch_and_if_empty_receive_new_batch_of_nsprs_and_load_one()
            cnodes_description = self.infrastructure_manager.describe()
            info = "moved-to-next-nspr" #TODO remove later if needed
        else:
            try:
                self.id_of_vnf_to_place, self.requirements_of_vnf_to_place = next(self.nspr_vnfs)
                cnodes_description = self.infrastructure_manager.describe() #Get Infrastruction information 
            except:
                # means ongoing NSPR's last VNF is already successfully processed : move ongoing NSPR into running NSPRs
                self.nsprs_lifecycle_manager.add_to_running_nsprs(self.ongoing_nspr) # successful NSPR
                self.number_of_successful_nsprs_in_batch += 1
                # next waiting NSPR needs to be loaded
                
                done = self.load_a_nspr_from_current_batch_and_if_empty_receive_new_batch_of_nsprs_and_load_one()
                cnodes_description = self.infrastructure_manager.describe()
                info = "moved-to-next-nspr" #TODO remove later if needed
        # print([cnodes_description, self.requirements_of_vnf_to_place])
        return [cnodes_description, self.requirements_of_vnf_to_place], reward, done, info #TODO not placed has replaced done

    def close(self):
        pass

    def iterative_nspr_vnfs_descriptions(self):
        vnfs_descriptions = self.ongoing_nspr.describe_vnfs()
        for vnf_id in range(len(vnfs_descriptions)):
            yield vnf_id+1, vnfs_descriptions[vnf_id]
    
    def place(self, vnf_id, vnf_requirements, cnode_id):
        # this function checks the placeability of the vnf (whose requirements are provided) on the cnode (whose id is provided)
        # if successful placement: information on placements and matchings are added into nspr
        placed = True
        mbfs_path = None
        reward = 0.0
        if vnf_id == 1:
            # we just need to check vnf_id can be place on cnode_id (no matching verification as it's first VNF)
            if self.infrastructure_manager.is_vnf_placeable(vnf_requirements, cnode_id, self.ongoing_nspr.nsprtype):
                placed = True
            else:
                placed = False
        else:
            # from second VNF, there are three possible cases
            # case 1 : VNF vnf_id is not placeable on cnode_id
            # case 2 : VNF vnf_id is placeable on cnode_id which is the same proposed for precedent VNF (vnf_id-1) meaning VNFs vnf_id and vnf_id-1 are on same cnode_id (no matching verification)
            # case 3 : VNF vnf_id is placeable on cnode_id which is different from the precedent VNF (vnf_id-1)' cnode meaning VNF vnf_id should be placeable on cnode_id AND there should be a path to link VNF vnf_id-1 cnode to the one of VNF vnf_id
            if self.infrastructure_manager.is_vnf_placeable(vnf_requirements, cnode_id, self.ongoing_nspr.nsprtype):
                if self.ongoing_nspr.get_placement(vnf_id-1) != "s"+str(cnode_id): # case 3
                    mbfs_path = self.infrastructure_manager.found_a_valid_path_between(self.ongoing_nspr.get_placement(vnf_id-1), "s"+str(cnode_id), vnf_requirements[-1], self.ongoing_nspr.nsprtype)
                    if mbfs_path is not None:
                        placed = True
                    else:
                        placed = False
                else: # case 2
                    placed = True
            else: # case 1
                placed = False
        #-----------------------------------------------------------------------
        if placed:
            self.ongoing_nspr.set_placement(vnf_id, cnode_id) # set placement information
            cnode_resources = self.infrastructure_manager.get_resources(cnode_id)
            self.ongoing_nspr.set_satisfied_resources( vnf_id, self.infrastructure_manager.place_vnf(vnf_requirements, cnode_id) ) # concretely place VNF implying cnode resources update
            if mbfs_path is not None:
                bw_reward = 1.0 / (len(mbfs_path) - 1)
                self.ongoing_nspr.set_matching(vnf_id, mbfs_path) # set matching information
                self.ongoing_nspr.set_satisfied_bw(vnf_id, self.infrastructure_manager.allocate_path(mbfs_path, vnf_requirements[-1]))
            else:
                bw_reward = 1.0
            # reward = 100.0 * bw_reward * ((cnode_resources[0]/self.cnodes_resources_upper_bounds[0])+(cnode_resources[1]/self.cnodes_resources_upper_bounds[1])+(cnode_resources[2]/self.cnodes_resources_upper_bounds[2]))
            reward = 100.0 * bw_reward * ((cnode_resources[0]/self.cnodes_resources_upper_bounds[0])*(cnode_resources[1]/self.cnodes_resources_upper_bounds[1])*(cnode_resources[2]/self.cnodes_resources_upper_bounds[2]))
        else:
            reward = -100.0
        return placed, reward
    
    def load_a_nspr_from_current_batch_and_if_empty_receive_new_batch_of_nsprs_and_load_one(self):
        # retrieve a waiting NSPR (allocability and flexibility are used here), verify it's different from None and load it
        episode_should_be_stopped = False
        self.ongoing_nspr = self.nsprs_lifecycle_manager.retrieve_a_waiting_nspr()
        if self.ongoing_nspr is None: # end of current batch of waiting NSPRs
            self.trigger_simulation_clock()
            if self.number_of_successful_nsprs_in_batch == 0:
                episode_should_be_stopped = True
            else:
                self.number_of_successful_nsprs_in_batch = 0
        while self.ongoing_nspr is None:
            self.nsprs_lifecycle_manager.add_to_waiting_nsprs( self.nsprs_generator.generate() )
            self.ongoing_nspr = self.nsprs_lifecycle_manager.retrieve_a_waiting_nspr()
        # loading next NSPR to be processed
        self.nspr_vnfs = self.iterative_nspr_vnfs_descriptions()
        self.id_of_vnf_to_place, self.requirements_of_vnf_to_place = next(self.nspr_vnfs)
        return episode_should_be_stopped
    
    def trigger_simulation_clock(self):
        # update nsprs' lifecycle by decrementing running nsprs' remaining durations
        # 1) decrement running NSPRs duration by 1
        # 2) retrieve terminated NSPRs (if any)
        # 3) deallocate their resources
        # 4) delete their information about placement and matchings
        nsprs_to_deallocate = self.nsprs_lifecycle_manager.decrement_running_nsprs_durations(keep_terminated_nsprs_information=self.keep_information)
        for nspr in nsprs_to_deallocate:
            self.infrastructure_manager.deallocate_whole_nspr(nspr)