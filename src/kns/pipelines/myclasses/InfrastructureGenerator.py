import copy
import numpy
import networkx

class InfrastructureGenerator:
    def __init__(self, parameters) -> None:
        self.infrastructure = int(parameters["infrastructure"]) ; assert int(parameters["infrastructure"]) in [1]
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
        self.min_cpu = parameters["min_cpu"]
        self.max_cpu = parameters["max_cpu"]
        self.min_ram = parameters["min_ram"]
        self.max_ram = parameters["max_ram"]
        self.min_stor = parameters["min_stor"]
        self.max_stor = parameters["max_stor"]
        self.cnodePl_min_bw = parameters["cnodePl_min_bw"]
        self.cnodePl_max_bw = parameters["cnodePl_max_bw"]
        self.corePl_min_bw = parameters["corePl_min_bw"]
        self.corePl_max_bw = parameters["corePl_max_bw"]
        self.min_latency = parameters["min_latency"]
        self.max_latency = parameters["max_latency"]
        #-------------------------------------------
        self.backup_of_infrastructure = None

    def generate(self):
        # returns a NetworkX-like object representing the infrastructure
        if (not self.is_for_train) and (self.backup_of_infrastructure is not None):
            return copy.deepcopy(self.backup_of_infrastructure)
        if self.infrastructure == 1:
            self.backup_of_infrastructure = self.infrastructure1()
        #--------------------------------------------------
        return copy.deepcopy(self.backup_of_infrastructure)
    
    def reset(self):
        if self.is_for_train:
            self.current_seed += 1
            self.backup_of_infrastructure = None
        self.numpy_gen = numpy.random.default_rng(self.current_seed)
        

    def infrastructure1(self):
        infrastructure = networkx.Graph()
        # create computing nodes
        for i in range(1,7):
            cpu_value = self.numpy_gen.uniform(self.min_cpu,self.max_cpu)
            ram_value = self.numpy_gen.uniform(self.min_ram,self.max_ram)
            stor_value = self.numpy_gen.uniform(self.min_stor,self.max_stor)
            infrastructure.add_node("s"+str(i), cpu=cpu_value, initial_cpu=cpu_value, ram=ram_value, initial_ram=ram_value, stor=stor_value, initial_stor=stor_value, load=0.0)
        # create switches
        for i in range(1,4):
            infrastructure.add_node("sw"+str(i))
        # create routers
        for i in range(1,5):
            infrastructure.add_node("r"+str(i))
        # link computing nodes to switches
        switch_index = 1
        for i in range(1,7):
            bw_value = self.numpy_gen.uniform(self.cnodePl_min_bw,self.cnodePl_max_bw)
            infrastructure.add_edge("s"+str(i), "sw"+str(switch_index), bw=bw_value)
            infrastructure.nodes["s"+str(i)]["initial_bw"] = bw_value
            if i%2==0:
                switch_index += 1
        # link switches to their routers
        infrastructure.add_edge("sw1", "r1", bw=self.numpy_gen.uniform(self.corePl_min_bw,self.corePl_max_bw))
        infrastructure.add_edge("sw2", "r3", bw=self.numpy_gen.uniform(self.corePl_min_bw,self.corePl_max_bw))
        infrastructure.add_edge("sw3", "r4", bw=self.numpy_gen.uniform(self.corePl_min_bw,self.corePl_max_bw))
        # link routers between themselves
        for i in range(1,5):
            for j in range(i+1,5):
                infrastructure.add_edge("r"+str(i), "r"+str(j), bw=self.numpy_gen.uniform(self.corePl_min_bw,self.corePl_max_bw))
        # return final result
        return infrastructure