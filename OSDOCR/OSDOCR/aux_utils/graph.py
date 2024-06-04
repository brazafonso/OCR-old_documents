from matplotlib import pyplot as plt
import networkx as nx
import pandas as pd

class Graph:
    '''Class to represent a graph'''

    def __init__(self,nodes:list['Node']=None):
        self.nodes = nodes if nodes else []

    def __str__(self):
        n_edges = len(self.get_edges())
        return f'Graph with {len(self.nodes)} nodes and {n_edges} edges'

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self.nodes)

    def __contains__(self,node:'Node'):
        return node in self.nodes

    def __getitem__(self,index:int):
        return self.nodes[index]


    def add_node(self,node:'Node'):
        if not self.contains(node):
            self.nodes.append(node)

    def contains(self,node:'Node'):
        '''Returns True if node is in self.nodes'''
        for n in self.nodes:
            if n.id == node.id:
                return True
        return False
    
    def contains_id(self,node_id:int):
        '''Returns True if node_id is in self.nodes'''
        for n in self.nodes:
            if n.id == node_id:
                return True
        return False

    def is_connected(self,node:int,only_parents:bool=False,only_children:bool=True):
        '''Returns True if node is connected to the graph\n
        Recursively checks if node is in self.parents or self.children'''
        for n in self.nodes:
            if n.is_connected(node,only_parents,only_children):
                return True
        return False

    def get_node(self,node:int):
        '''Returns node if node is connected to the graph'''
        for n in self.nodes:
            if node == n.id:
                return n
        return None
    
    def get_edges(self,only_children:bool=True)->list['Edge']:
        '''Returns a list of all edges in the graph'''
        edges = []
        for node in self.nodes:
            edges.extend(node.children_edges)
            if not only_children:
                edges.extend(node.parent_edges)
        return edges
    
    def to_data_frame(self):
        '''Returns a pandas DataFrame with the graph nodes and edges'''
        edges = self.get_edges()
        edges = [(edge.source.id,edge.target.id,edge.weight) for edge in edges]
        df = pd.DataFrame(edges,columns=['source','target','weight'])
        return df

    def pretty_print(self):
        '''Print graph and its nodes using networkx'''
        G = nx.from_pandas_edgelist(self.to_data_frame(),'source','target','weight')
        pos = nx.spring_layout(G)
        nx.draw(G,pos,with_labels=True)
        plt.show()


    def self_print(self):
        '''Print graph and its nodes'''
        for node in self.nodes:
            print(node.id,':',node.children_edges,'|',node.parent_edges)


    def clean_graph(self,visit_order:list[int]=None):
        '''Remove transitive edges from graph\n
        Needs to follow the order of visit of the graph, so as not to remove transitive edges that are not transitive'''
        if not visit_order:
            visit_order = [node.id for node in self.nodes]

        for node_id in visit_order:
            node = self.get_node(node_id)
            edges = node.children_edges.copy()
            for edge in edges:
                source = edge.source
                target = edge.target
                connection_nodes_ids = target.connection_points(source.id,only_parents=True,only_children=False,visited=[],ignore_self=True)
                connection_nodes = [self.get_node(node_id) for node_id in connection_nodes_ids]
                for connection_node in connection_nodes:
                    # if target is connected to source through other nodes, remove edge
                    ## unless connection node is in source's children
                    if not source.in_children(connection_node):
                        source.remove_edge(edge)

    def narrow_parents(self):
        '''Remove edges from nodes that have more than one parent'''
        connections = []
        for node in self.nodes:
            for edge in node.children_edges:
                total_weight = edge.weight
                target = edge.target
                target_edge = target.get_edge(node.id,child=False)
                if target_edge:
                    total_weight += target_edge.weight
                connections.append((total_weight,edge))

        connections.sort(key=lambda x: x[0],reverse=True)
        visited = []
        # narrow parents
        ## choose connection with highest weight
        ## remove other parent connections for respective node
        ## if more than one connection has the same weight, leave them
        for weight,edge in connections:
            if edge.source.id not in visited:
                visited.append(edge.source.id)
                # print('Verifying edge',edge)
                for other_connection in connections:
                    other_edge = other_connection[1]
                    # print('\t'*1,'Other edge',other_edge)
                    if other_edge == edge:
                        continue
                    if other_edge.target.id == edge.target.id:
                        # print('\t'*2,'Comparing',other_edge,other_connection[0],edge,weight)
                        if other_connection[0] < weight and other_connection[0]/weight < 0.5:
                            # print('\t'*3,'removing',other_edge)
                            edge.target.remove_edge(other_edge)
                        elif other_connection[0] > weight and weight/other_connection[0] < 0.5:
                            # print('\t'*3,'removing',edge)
                            edge.target.remove_edge(edge)




class Node:
    '''Class to represent a node'''

    def __init__(self,id:int,parents:list['Edge']=None,children:list['Edge']=None,value=None):
        self.id = id
        self.parent_edges = parents if parents else []
        self.children_edges = children if children else []
        self.value = value

    def __str__(self):
        return f'{self.id}'

    def add_parent_edge(self,parent:'Node',weight:float=0):
        if not self.in_parents(parent):
            edge = Edge(parent,self,weight)
            self.parent_edges.append(edge)
            parent.add_child_edge(self,weight)

    def add_child_edge(self,child:'Node',weight:float=0):
        if not self.in_children(child):
            edge = Edge(self,child,weight)
            self.children_edges.append(edge)
            child.add_parent_edge(self,weight)

    def in_children(self,node:'Node'):
        '''Returns True if node is in self.children'''
        for child_edge in self.children_edges:
            child = child_edge.target
            if child.id == node.id:
                return True
        return False
    
    def in_parents(self,node:'Node'):
        '''Returns True if node is in self.parents'''
        for parent_edge in self.parent_edges:
            parent = parent_edge.source
            if parent == node:
                return True
        return False
    
    def get_edge(self,node:int,child:bool=True)->'Edge':
        '''Returns edge between self and node\n
        If child is True, returns edge from self.children_edges\n
        If child is False, returns edge from self.parent_edges'''
        if child:
            for edge in self.children_edges:
                if edge.target.id == node:
                    return edge
        else:
            for edge in self.parent_edges:
                if edge.source.id == node:
                    return edge
        return None
    
    def remove_edge(self,edge:'Edge'):
        '''Remove edge from self.children_edges or self.parent_edges\n
        Removes edge from both target and source'''
        # print('removing edge',edge)
        source = edge.source
        target = edge.target
        # print('source',source)
        # print('target',target)
        # print('self',self)
        if source.id == self.id:
            # print('searching for child',target.id)
            for child_edge in source.children_edges:
                if child_edge.target.id == target.id :
                    source.children_edges.remove(child_edge)
                    # print('removing child',child_edge)
                    edge.target.remove_edge(child_edge)
                    break
        elif target.id == self.id:
            # print('searching for parent',source.id)
            for parent_edge in target.parent_edges:
                if parent_edge.source.id == source.id:
                    target.parent_edges.remove(parent_edge)
                    # print('removing parent',parent_edge)
                    edge.source.remove_edge(parent_edge)
                    break

    def is_connected(self,node:int,only_parents:bool=False,only_children:bool=True,visited:list=[],ignore_self:bool=False):
        '''Returns True if node is connected to self\n
        Recursively checks if node is in self.parents or self.children'''
        if self.id == node:
            return True

        if self.id in visited:
            return False
        
        parent_edges = self.parent_edges.copy()
        children_edges = self.children_edges.copy()

        if ignore_self:
            parent_edges = [edge for edge in parent_edges if edge.source.id != node]
            children_edges = [edge for edge in children_edges if edge.target.id != node]
        
        visited.append(self.id)
        # check in direct parents
        if not only_children:
            for parent_edge in parent_edges:
                parent = parent_edge.source
                if parent.id == node:
                    return True
                
        # check in direct children
        if not only_parents:
            for child_edge in children_edges:
                child = child_edge.target
                if child.id == node:
                    return True

        # check if children or parents are connected to node
        if not only_children:
            for parent_edge in parent_edges:
                parent = parent_edge.source
                if parent.is_connected(node,only_parents,only_children,visited):
                    return True
                
        if not only_parents:
            for child_edge in children_edges:
                child = child_edge.target
                if child.is_connected(node,only_parents,only_children,visited):
                    return True
                
        return False
    
    def connection_points(self,node:int,only_parents:bool=False,only_children:bool=True,visited:list=[],ignore_self:bool=False):
        '''Returns list of nodes that connect self to node\n'''
        connection_nodes = []

        if self.id == node:
            print('self',visited,self.id)
            return []

        if self.id in visited:
            return []
        
        parent_edges = self.parent_edges.copy()
        children_edges = self.children_edges.copy()

        if ignore_self:
            parent_edges = [edge for edge in parent_edges if edge.source.id != node]
            children_edges = [edge for edge in children_edges if edge.target.id != node]
        
        visited.append(self.id)
        # check in direct parents
        if not only_children:
            for parent_edge in parent_edges:
                parent = parent_edge.source
                if parent.id == node:
                    print('parent',visited,self.id,parent.id)
                    connection_nodes.append(self.id)
                    break
                
        # check in direct children
        if not only_parents:
            for child_edge in children_edges:
                child = child_edge.target
                if child.id == node:
                    print('child',visited,self.id,child.id)
                    connection_nodes.append(self.id)
                    break

        # check if children or parents are connected to node
        if not only_children:
            for parent_edge in parent_edges:
                parent = parent_edge.source
                connection_nodes += parent.connection_points(node,only_parents,only_children,visited)
                    
                
        if not only_parents:
            for child_edge in children_edges:
                child = child_edge.target
                connection_nodes += child.connection_points(node,only_parents,only_children,visited)
                
        return connection_nodes
    
    
    def get_node(self,node:int,only_parents:bool=False,only_children:bool=True):
        '''Returns node if node is connected to self\n
        Recursively checks if node is in self.parents or self.children'''
        if self.id == node:
            return self

        # check in direct parents
        if not only_children:
            for parent_edge in self.parent_edges:
                parent = parent_edge.source
                if parent.id == node:
                    return parent
                
        # check in direct children
        if not only_parents:
            for child_edge in self.children_edges:
                child = child_edge.target
                if child.id == node:
                    return child

        # check if children or parents are connected to node
        if not only_children:
            for parent_edge in self.parent_edges:
                node = parent_edge.source.get_node(node,only_parents,only_children)
                if node:
                    return node
        if not only_parents:
            for child_edge in self.children_edges:
                node = child_edge.target.get_node(node,only_parents,only_children)
                if node:
                    return node
                
        return None
    
    def pretty_print(self,indent:int=0,visited:list=[]):
        '''Print node and its children'''
        if self not in visited:
            visited.append(self)
            print(' '*indent + str(self))
            for child_edge in self.children_edges:
                child = child_edge.target
                child.pretty_print(indent+2,visited)

    def self_print(self):
        '''Print node and its children'''
        indent = (len(self.children_edges)//2) * 2
        print(f"{indent*' '}{self.id}")
        indent = 2
        for child_edge in self.children_edges:
            child = child_edge.target
            print(f"{indent*' '}{child.id}", end='')
        print()

    def get_connections(self,only_parents:bool=False,only_children:bool=True,visited:list=[]):
        '''Returns a list of all nodes connected to self'''
        connected = []
        if self.id not in visited:
            visited.append(self.id)
            connected.append(self)
            for child_edge in self.children_edges:
                child = child_edge.target
                connected.extend(child.get_connections(only_parents,only_children,visited))
            if not only_children:
                for parent_edge in self.parent_edges:
                    parent = parent_edge.source
                    connected.extend(parent.get_connections(only_parents,only_children,visited))
        return connected

                
class Edge:
    '''Class to represent an edge'''

    def __init__(self,source:'Node',target:'Node',weight:float=0):
        self.source = source
        self.target = target
        self.weight = weight

    def __str__(self):
        return f'{self.source.id} -> {self.target.id} ({self.weight})'

    def __repr__(self):
        return self.__str__()

    def __eq__(self,other):
        return self.source == other.source and self.target == other.target and self.weight == other.weight

    def __hash__(self):
        return hash((self.source,self.target))
    