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
        if not self.in_graph(node):
            self.nodes.append(node)

    def in_graph(self,node:'Node'):
        '''Returns True if node is in self.nodes'''
        for n in self.nodes:
            if n.id == node.id:
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
    
    def get_edges(self)->list['Edge']:
        '''Returns a list of all edges in the graph'''
        edges = []
        for node in self.nodes:
            edges.extend(node.children_edges)
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
            print(node.id,':',node.children_edges)


    def clean_graph(self):
        '''Remove transitive edges from graph'''
        edges = self.get_edges()
        for edge in edges:
            source = edge.source
            target = edge.target
            print(edge)
            if target.is_connected(source.id,only_parents=True,only_children=False,visited=[],ignore_self=True):
                source.remove_edge(edge)



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
            if child == node:
                return True
        return False
    
    def in_parents(self,node:'Node'):
        '''Returns True if node is in self.parents'''
        for parent_edge in self.parent_edges:
            parent = parent_edge.source
            if parent == node:
                return True
        return False
    
    def remove_edge(self,edge:'Edge'):
        '''Remove edge from self.children_edges or self.parent_edges\n
        Removes edge from both target and source'''
        if edge in self.children_edges:
            print('removing child',edge)
            self.children_edges.remove(edge)
            parent_edge = Edge(edge.target,self)
            edge.target.remove_edge(parent_edge)
        elif edge in self.parent_edges:
            print('removing parent',edge)
            self.parent_edges.remove(edge)
            child_edge = Edge(self,edge.target)
            edge.target.remove_edge(child_edge)

    def is_connected(self,node:int,only_parents:bool=False,only_children:bool=True,visited:list=[],ignore_self:bool=False):
        '''Returns True if node is connected to self\n
        Recursively checks if node is in self.parents or self.children'''
        if self.id == node:
            print('self',visited,self.id)
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
                    print('parent',visited,self.id,parent.id)
                    return True
                
        # check in direct children
        if not only_parents:
            for child_edge in children_edges:
                child = child_edge.target
                if child.id == node:
                    print('child',visited,self.id,child.id)
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
    