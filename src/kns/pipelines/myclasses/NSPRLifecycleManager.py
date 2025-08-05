import copy

class NSPRLifecycleManager:
    def __init__(self) -> None:
        self.nsprs_waiting = [] # contains nsprs waiting to be processed
        self.nsprs_running = [] # contains currently deployed (running) nsprs
        self.nsprs_terminated_after_running = [] # contains nsprs terminated successfully after their deployment duration satisfied
        self.nsprs_terminated_after_fail = [] # contains nsprs which were not deployable
        self.nsprs_delayed = [] # contains nsprs which were delayed for re-processing in next time slot
    
    def add_to_waiting_nsprs(self, new_nsprs):
        for nspr in new_nsprs: nspr.update_status_chain("waiting")
        # new_nsprs is a list of nsprs
        if len(self.nsprs_delayed) > 0:
            for nspr in self.nsprs_delayed:
                new_nsprs.append(nspr)
            del self.nsprs_delayed[:]
        self.nsprs_waiting.append( new_nsprs )
    
    def retrieve_a_waiting_nspr(self, nspr_selector=None):
        if len(self.nsprs_waiting) > 0:
            if len(self.nsprs_waiting[0]) > 0:
                if nspr_selector is None: # FIFO based selection
                    self.nsprs_waiting[0][0].update_status_chain("processing")
                    return self.nsprs_waiting[0].pop(0)
                else: # ALLOCABILITY+FLEXIBILITY based selection                    
                    slice_id,selected_nspr = nspr_selector.choose_best_slice(copy.deepcopy(self.nsprs_waiting[0]))
                    # print(f"id : {slice_id}")
                    selected_nspr.update_status_chain("processing")
                    self.nsprs_waiting[0].pop(slice_id)
                    return selected_nspr
            else: # batch self.nsprs_waiting[0] has 0 remaining nspr and should be removed
                self.nsprs_waiting.pop(0)
                self.retrieve_a_waiting_nspr(nspr_selector)
        else:
            return None
    
    def add_to_delayed_nsprs(self, nspr):
        nspr.update_status_chain("delayed")
        nspr.unset_placements_and_matchings() # delete information about placement and matchings in NSPR
        nspr.reinitialize_duration()
        self.nsprs_delayed.append(nspr)

    def add_to_running_nsprs(self, nspr):
        nspr.update_status_chain("running")
        self.nsprs_running.append(nspr)

    def decrement_running_nsprs_durations(self, keep_terminated_nsprs_information):
        # will decrement the remaining duration of each NSPR in running nsprs list then those having a remaining duration of 0 will be moved to nsprs_terminated_after_running and removed from running list
        # also return moved NSPRs (they are required for restoring they resources)
        nsprs_to_deallocate = []
        for nspr in self.nsprs_running:
            nspr.decrement_remaining_duration()
            if nspr.can_continue_running() == False:
                if not keep_terminated_nsprs_information:
                    nspr.unset_placements_and_matchings() # delete placements and matchings information
                nsprs_to_deallocate.append( copy.deepcopy(nspr) )
                nspr.update_status_chain("successTerminate")
                self.nsprs_terminated_after_running.append( copy.deepcopy(nspr) )
                self.nsprs_running.remove(nspr)
        return nsprs_to_deallocate

    def add_to_terminated_nsprs_after_fail(self, nspr):
        nspr.update_status_chain("failTerminate")
        self.nsprs_terminated_after_fail.append(nspr)
    
    def running_and_successfully_terminated_nsprs(self):
        return len(self.nsprs_running) + len(self.nsprs_terminated_after_running)
    
    def running_nsprs(self):
        return len(self.nsprs_running)
    
    def successfully_terminated_nsprs(self):
        return len(self.nsprs_terminated_after_running)
    
    def failed_nsprs(self):
        return len(self.nsprs_terminated_after_fail)
    
    def reset(self):
        self.nsprs_waiting = []
        self.nsprs_running = []
        self.nsprs_terminated_after_running = []
        self.nsprs_terminated_after_fail = []
        self.nsprs_delayed = []
        self.received_nsprs_batch_counter = 1