import networkx

class InfrastructureManager:
    def __init__(self, infrastructure_generator) -> None:
        self.infrastructure_generator = infrastructure_generator
        self.infrastructure_to_manage = self.infrastructure_generator.generate() # infrastructure_to_manage is a NetworkX-like graph
        self.number_of_computing_nodes = len([cnode for cnode in self.infrastructure_to_manage.nodes.data("cpu") if cnode[1] is not None])
    
    def get_resources(self, cnode_id):
        # returns CPU,RAM,STORAGE,BANDWIDTH of cnode cnode_id
        return [
            self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["cpu"],
            self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["ram"],
            self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["stor"],
            sum([self.infrastructure_to_manage["s"+str(cnode_id)][n]["bw"] for n in networkx.neighbors(self.infrastructure_to_manage,"s"+str(cnode_id))])
        ]
    
    def get_resources_upper_bounds(self):
        # return upper bounds of intervals used to set comp. nodes initial resources
        return [
            self.infrastructure_generator.max_cpu,
            self.infrastructure_generator.max_ram,
            self.infrastructure_generator.max_stor
        ]

    def describe(self):
        # returns a list describing each computing node (CPU,RAM,STORAGE,BANDWIDTH)
        resources = []
        for cnode_id in range(1,self.number_of_computing_nodes+1):
            resources.extend( self.get_resources(cnode_id) )
        return resources
    
    # mBFS functions
    def is_vnf_placeable(self, vnf_requirements, cnode_id, nsprtype):
        # verify all resources on cnode_id are higher or equal to vnf resource requirements
        if nsprtype == 'hard':
            if self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["cpu"] >= vnf_requirements[0] and \
            self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["ram"] >= vnf_requirements[1] and \
            self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["stor"] >= vnf_requirements[2]:
                return True
            else:
                return False
        elif nsprtype == 'soft':
            if self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["cpu"] > 0 and \
            self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["ram"] > 0 and \
            self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["stor"] > 0:
                return True
            else:
                return False

    def place_vnf(self, vnf_requirements, cnode_id):
        # simulate a VNF placement on cnode_id by allocating resources and returns unsatisfied resources
        #---cpu---
        allocated_cpu = min(self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["cpu"], vnf_requirements[0])
        self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["cpu"] -= allocated_cpu
        #---ram---
        allocated_ram = min(self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["ram"], vnf_requirements[1])
        self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["ram"] -= allocated_ram
        #---stor---
        allocated_stor = min(self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["stor"], vnf_requirements[2])
        self.infrastructure_to_manage.nodes["s"+str(cnode_id)]["stor"] -= allocated_stor
        return [allocated_cpu, allocated_ram, allocated_stor]

    def remove_vnf(self, vnf_requirements, cnode_name):
        self.infrastructure_to_manage.nodes[cnode_name]["cpu"] += vnf_requirements[0]
        self.infrastructure_to_manage.nodes[cnode_name]["ram"] += vnf_requirements[1]
        self.infrastructure_to_manage.nodes[cnode_name]["stor"] += vnf_requirements[2]

    def minimum_bandwidth_of_path(self, path):
        minimum_bandwidth = self.infrastructure_to_manage[path[0]][path[1]]["bw"]
        for i in range(len(path)-1):
            segment_bandwith = self.infrastructure_to_manage[path[i]][path[i+1]]["bw"]
            if segment_bandwith < minimum_bandwidth:
                minimum_bandwidth = segment_bandwith
        return minimum_bandwidth
    def found_a_valid_path_between(self, cnode_id1, cnode_id2, bandwidth, nsprtype):
        # mBFS : return a list of the nodes in the path if path found, otherwise return None along with guaranteed bandwidth
        assert cnode_id1 != cnode_id2
        paths = []
        path = None
        neighbors = []
        node_name = cnode_id1
        paths.append([cnode_id1])
        while len(paths) != 0:
            path = paths.pop(0)
            node_name = path[-1]
            if node_name == cnode_id2:
                return path
            for neighbor in networkx.neighbors(self.infrastructure_to_manage,node_name):
                if nsprtype == 'hard':
                    if neighbor not in path and self.infrastructure_to_manage[node_name][neighbor]["bw"]>=bandwidth:
                        neighbors.append(neighbor)
                elif nsprtype == 'soft':
                    if neighbor not in path and self.infrastructure_to_manage[node_name][neighbor]["bw"]>0:
                        neighbors.append(neighbor)
            for neighbor in neighbors:
                paths.append(path+[neighbor])
            del neighbors[:]
        return None

    def allocate_path(self, found_path, bandwidth):
        bandwidth_allocated = min(bandwidth, self.minimum_bandwidth_of_path(found_path))
        for i in range(len(found_path)-1):
            self.infrastructure_to_manage[found_path[i]][found_path[i+1]]["bw"] -= bandwidth_allocated
        return bandwidth_allocated # satisfied bandwidth

    def deallocate_path(self, found_path, bandwidth):
        for i in range(len(found_path)-1):
            self.infrastructure_to_manage[found_path[i]][found_path[i+1]]["bw"] += bandwidth
    
    def deallocate_whole_nspr(self, nspr):
        # vnfs_requirements = nspr.describe_vnfs() # vnfs_requirements is a list of [CPU,RAM,STORAGE,BANDWIDTH] per VNF
        for vnf_id in range(1,nspr.n_vnfs()+1):
            if nspr.get_placement(vnf_id) is not None:
                self.remove_vnf(nspr.get_satisfied_resources(vnf_id), nspr.get_placement(vnf_id))
            else:
                break
            if nspr.get_matching(vnf_id) not in ["NoNeed",None]:
                self.deallocate_path(nspr.get_matching(vnf_id), nspr.get_satisfied_bw(vnf_id))

    def reset(self):
        self.infrastructure_generator.reset()
        self.infrastructure_to_manage = self.infrastructure_generator.generate() # infrastructure_to_manage is a NetworkX-like graph
        self.number_of_computing_nodes = len([cnode for cnode in self.infrastructure_to_manage.nodes.data("cpu") if cnode[1] is not None])