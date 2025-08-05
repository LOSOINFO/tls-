import numpy
import networkx

class NSPR:
    def __init__(self, id, priority, duration, nsprtype) -> None:
        self.nspr = networkx.DiGraph(name=id)
        self.priority = priority
        assert duration > 0
        self.duration = duration # integer greater than 0 initially
        self.remaining_duration = self.duration
        self.nsprtype = nsprtype # 'hard' or 'soft' requirements
        self.status_chain = ""
    
    def update_status_chain(self, new_status):
        if self.status_chain == "": self.status_chain += new_status
        else: self.status_chain += "-"+new_status
    
    def get_status_chain(self):
        return self.status_chain

    def get_id(self):
        return self.nspr.name
    
    def get_priority(self):
        return self.priority
    
    def get_initial_duration(self):
        return self.duration
    
    def reinitialize_duration(self):
        self.remaining_duration = self.duration

    def get_nspr_type(self):
        return self.nsprtype
    
    def decrement_remaining_duration(self):
        assert self.remaining_duration > 0
        self.remaining_duration = self.remaining_duration - 1
    
    def can_continue_running(self):
        if self.remaining_duration > 0:
            return True
        else:
            return False
    
    def add_vnf(self, rq_cpu, rq_ram, rq_stor, rq_bw):
        number_of_vnfs = len(self.nspr)
        if number_of_vnfs == 0:
            self.nspr.add_node("vnf1", rq_cpu=rq_cpu, rq_ram=rq_ram, rq_stor=rq_stor, placement=None, satisf_res=None)
        else:
            self.nspr.add_node("vnf"+str(number_of_vnfs+1), rq_cpu=rq_cpu, rq_ram=rq_ram, rq_stor=rq_stor, placement=None, satisf_res=None)
            self.nspr.add_edge("vnf"+str(number_of_vnfs), "vnf"+str(number_of_vnfs+1), rq_bw=rq_bw, matching=None, satisf_bw=None)
    
    def n_vnfs(self):
        return len(self.nspr)
    
    def describe_vnfs(self):
        all_descriptions = []
        for i in range(1,len(self.nspr)+1):
            vnf_desc = []
            vnf_desc.append(self.nspr.nodes["vnf"+str(i)]["rq_cpu"])
            vnf_desc.append(self.nspr.nodes["vnf"+str(i)]["rq_ram"])
            vnf_desc.append(self.nspr.nodes["vnf"+str(i)]["rq_stor"])
            if i == 1: vnf_desc.append(0.0)
            else: vnf_desc.append(self.nspr["vnf"+str(i-1)]["vnf"+str(i)]["rq_bw"])
            #---------------
            all_descriptions.append(vnf_desc)
        return all_descriptions
    
    def set_placement(self, vnf_id, cnode_id):
        self.nspr.nodes["vnf"+str(vnf_id)]["placement"] = "s"+str(cnode_id)
    
    def get_placement(self, vnf_id):
        return self.nspr.nodes["vnf"+str(vnf_id)]["placement"]
    
    def set_satisfied_resources(self, vnf_id, cpu_ram_stor):
        # set amounts of satisfied cpu,ram,storage relative to the total amounts required
        self.nspr.nodes["vnf"+str(vnf_id)]["satisf_res"] = cpu_ram_stor

    def get_satisfied_resources(self, vnf_id):
        # returns amounts of satisfied cpu,ram,storage relative to the total amounts required
        return self.nspr.nodes["vnf"+str(vnf_id)]["satisf_res"]
    
    def set_satisfied_bw(self, vnf_id, bandwidth):
        # set amount of satisfied bandwidth relative to the total amount required
        assert vnf_id >= 1
        # will match virtual link (vnf_id-1;vnf_id) to matching
        if vnf_id > 1:
            self.nspr["vnf"+str(vnf_id-1)]["vnf"+str(vnf_id)]["satisf_bw"] = bandwidth
    
    def get_satisfied_bw(self, vnf_id):
        assert vnf_id >= 1
        # returns amount of satisfied bandwidth relative to the total amount required
        if vnf_id == 1:
            return "NoNeed"
        else:
            return self.nspr["vnf"+str(vnf_id-1)]["vnf"+str(vnf_id)]["satisf_bw"]
    
    def set_matching(self, vnf_id, physical_path):
        assert vnf_id >= 1
        # will match virtual link (vnf_id-1;vnf_id) to physical_path
        if vnf_id > 1:
            self.nspr["vnf"+str(vnf_id-1)]["vnf"+str(vnf_id)]["matching"] = physical_path
    
    def get_matching(self, vnf_id):
        assert vnf_id >= 1
        # will get the matching of virtual link (vnf_id-1;vnf_id)
        if vnf_id == 1:
            return "NoNeed"
        else:
            return self.nspr["vnf"+str(vnf_id-1)]["vnf"+str(vnf_id)]["matching"]
    
    def unset_placements_and_matchings(self):
        for vnf_id in range(1,len(self.nspr)+1):
            if self.nspr.nodes["vnf"+str(vnf_id)]["placement"] is not None:
                self.nspr.nodes["vnf"+str(vnf_id)]["placement"] = None
                self.nspr.nodes["vnf"+str(vnf_id)]["satisf_res"] = None
                if vnf_id > 1:
                    self.nspr["vnf"+str(vnf_id-1)]["vnf"+str(vnf_id)]["matching"] = None
                    self.nspr["vnf"+str(vnf_id-1)]["vnf"+str(vnf_id)]["satisf_bw"] = None
            else:
                break


class NSPRGenerator:
    def __init__(self, parameters) -> None:
        # generation_law should be a function that generates an integer (number of nspr to be generated)
        #-------------------------------------------------------------------------------------------------
        assert parameters["is_for_train"] in [True,False]
        self.is_for_train = parameters["is_for_train"]
        if self.is_for_train:
            self.seed = parameters["train_seed"]
        else:
            self.seed = parameters["eval_seed"]
        self.current_seed = self.seed
        self.numpy_gen = numpy.random.default_rng(self.current_seed)
        #-------------------------------------------------------------------------------------------------
        self.rq_min_cpu = parameters["rq_min_cpu"]
        self.rq_max_cpu = parameters["rq_max_cpu"]
        self.rq_min_ram = parameters["rq_min_ram"]
        self.rq_max_ram = parameters["rq_max_ram"]
        self.rq_min_stor = parameters["rq_min_stor"]
        self.rq_max_stor = parameters["rq_max_stor"]
        self.rq_min_bw = parameters["rq_min_bw"]
        self.rq_max_bw = parameters["rq_max_bw"]
        self.min_vnfs = parameters["min_vnfs"] ; assert isinstance(self.min_vnfs, int)
        self.max_vnfs = parameters["max_vnfs"] ; assert isinstance(self.max_vnfs, int)
        self.min_duration = parameters["min_duration"] ; assert isinstance(self.min_duration, int)
        self.max_duration = parameters["max_duration"] ; assert isinstance(self.max_duration, int)
        self.possible_priorities = parameters["priorities"]
        self.possible_nsprtypes = parameters["nspr_types"]
        self.generation_law = lambda : numpy.random.randint(low=parameters["min_batch_nsprs"], high=parameters["max_batch_nsprs"]+1)
        self.id_counter = 1
    
    def generate(self):
        nsprs = []
        number_of_nsprs = self.generation_law() #TODO correct this as to make it being managed by the class itself based on user instruction
        assert isinstance(number_of_nsprs, int)
        for _ in range(number_of_nsprs):
            # create nspr
            nspr = NSPR(id="NSPR"+str(self.id_counter), priority=self.numpy_gen.choice(self.possible_priorities), duration=self.numpy_gen.integers(self.min_duration,self.max_duration+1), nsprtype=self.numpy_gen.choice(self.possible_nsprtypes))
            # determine number of vnfs in nspr
            n_vnfs = self.numpy_gen.integers(low=self.min_vnfs, high=self.max_vnfs+1)
            # create nspr's vnfs
            for _ in range(n_vnfs):
                nspr.add_vnf(rq_cpu=self.numpy_gen.uniform(self.rq_min_cpu,self.rq_max_cpu),
                             rq_ram=self.numpy_gen.uniform(self.rq_min_ram,self.rq_max_ram),
                             rq_stor=self.numpy_gen.uniform(self.rq_min_stor,self.rq_max_stor),
                             rq_bw=self.numpy_gen.uniform(self.rq_min_bw,self.rq_max_bw))
                pass
            nsprs.append(nspr)
            self.id_counter += 1
        return nsprs
    
    def reset(self):
        if self.is_for_train:
            self.current_seed += 1
        self.numpy_gen = numpy.random.default_rng(self.current_seed)
        self.id_counter = 1