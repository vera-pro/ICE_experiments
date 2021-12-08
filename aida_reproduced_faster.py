from collections import namedtuple

MentionEntry = namedtuple('MentionEntry', 'mention candidates')
CandidateEntry = namedtuple("CandidateEntry", 'candidate score')
NodeEntry = namedtuple('NodeEntry', 'name isEntity edges')
import pickle
from utils import *
from tqdm.auto import tqdm

from queue import PriorityQueue

try:
    relatedness_cache = pickle.load(open('/home/vprovat/EL_pickles/relatedness_cache.p', 'rb'))
    # storing WAT's relatedness values to avoid sending too many queries
except:
    relatedness_cache = {}

class MentionNode:
    def __init__(self, name):
        self.name = name
        self.edges = {}

    def add_edge(self, target_name, weight):
        # From this node to another
        if target_name in self.edges:
            print('Trying to add a duplicate edge from {0} to {1}'.format(self.name, target_name))
        self.edges[target_name] = weight

    def update_edge(self, target_name, weight):
        self.edges[target_name] = weight

    def remove_edge(self, target_name):
        if target_name in self.edges:
            self.edges.pop(target_name)

    def display(self):
        print('name: ', self.name)
        print('edges: ', self.edges)

class EntityNode:
    def __init__(self, name):
        self.name = name
        self.edges_entity = {}
        self.edges_mention = {}

    def add_edge(self, target_name, weight, mention_edge=True):
        if mention_edge:
            self.edges_mention[target_name] = weight
        else:
            self.edges_entity[target_name] = weight

    def update_edge(self, target_name, weight, mention_edge=True):
        if mention_edge:
            self.edges_mention[target_name] = weight
        else:
            self.edges_entity[target_name] = weight

    def remove_edge(self, target_name, mention_edge=True):
        if mention_edge:
            if target_name in self.edges_mention:
                self.edges_mention.pop(target_name)
        else:
            if target_name in self.edges_entity:
                self.edges_entity.pop(target_name)

    def display(self):
        print('name: ', self.name)
        print('edges_entity: ', self.edges_entity)
        print('edges_mention: ', self.edges_mention)


def weighted_degree_entity(node):
    # For an entity node
    res = sum(node.edges_mention[x] for x in node.edges_mention) + sum(node.edges_entity[x] for x in node.edges_entity)
    return res


def is_taboo(node, mention_nodes):
    # If an entity node is the last candidate for a mention, it's taboo
    target_mention_name = list(node.edges_mention.keys())[
        0]  # dirty but works: first (and usually only) mention linked to this candidate
    target_mention_node = None
    # looking for the mention node
    for ment_node in mention_nodes:
        if ment_node.name == target_mention_name:
            target_mention_node = ment_node
            break
    if not target_mention_node:
        print('failed to found a mention connected with ', node.name)
        return False

    return (len(target_mention_node.edges) == 1)


def disambiguate(mention_nodes, entity_nodes):
    '''
    Algorithm 1: Graph Disambiguation Algorithm
Input: weighted graph of mentions and entities
Output: result graph with one edge per mention
begin
    pre–processing phase;
    foreach entity do
        calculate distance to all mentions;
        keep the closest (5× mentions count)
        entities, drop the others;
    main loop;
    while graph has non-taboo entity do
        determine non-taboo entity node with lowest weighted degree,
        remove it and all its incident edges;
        if minimum weighted degree increased then
            set solution to current graph;
    post–processing phase;
        process solution by local search or full enumeration for best configuration;
    '''
    # an entity is taboo if it is the last candidate for a mention it is connected to

    # todo: add pre-processing

    # todo: try using heapq in the future, it will be probably faster
    weighted_degrees_q = PriorityQueue()
    weighted_degrees_sorted = sorted([(node, weighted_degree_entity(node)) for node in entity_nodes],
                                     key=lambda x: x[1])

    # todo: update weighted degree when removing a node

    max_num_iterations = len(weighted_degrees_sorted) * 2 # for debugging
    num_iterations = 0
    while len(entity_nodes) > len(mention_nodes) and num_iterations < max_num_iterations:
        num_iterations += 1
        # print("{0} entity nodes, {1} mention nodes".format(len(entity_nodes), len(mention_nodes)))
        ind_to_remove = 0 # current index of the node with minimum degree
        while is_taboo(weighted_degrees_sorted[ind_to_remove]) and ind_to_remove < len(weighted_degrees_sorted):
            ind_to_remove += 1

        if ind_to_remove < len(weighted_degrees_sorted):
            # removing a node
            node_to_remove = weighted_degrees_sorted

        for i, node in enumerate(entity_nodes):
            if is_taboo(node, mention_nodes):
                continue
            cur_degree = weighted_degree_entity(node)
            if cur_degree < min_degree:
                ind_to_remove = i
                min_degree = cur_degree

        if ind_to_remove != -1: # remove a node
            node_to_remove = entity_nodes[ind_to_remove]
            entity_nodes.pop(ind_to_remove)
            for mention_node in mention_nodes:
                mention_node.remove_edge(node_to_remove.name)

            for entity_node in entity_nodes:
                entity_node.remove_edge(node_to_remove.name, mention_edge=False)

    # todo: add post-processing
    if num_iterations == max_num_iterations:
        print("Got a fucking infinite loop!!!")
    return mention_nodes, entity_nodes

def relatedness(ent1, ent2, measure='pmi'):
    id1 = wat_wiki_id(ent1.name)
    id2 = wat_wiki_id(ent2.name)
    if measure in relatedness_cache:
        if id1 in relatedness_cache:
            if id2 in relatedness_cache[measure][id1]:
                return relatedness_cache[measure][id1][id2]

    # Asking the API for the result
    res = wat_relatedness_pairwise(id1, id2, measure)

    # Saving to cache
    if measure not in relatedness_cache:
        relatedness_cache[measure] = {}

    if id1 not in relatedness_cache[measure]:
        relatedness_cache[measure][id1] = {}
    if id2 not in relatedness_cache[measure]:
        relatedness_cache[measure][id2] = {}

    relatedness_cache[measure][id1][id2] =  res
    relatedness_cache[measure][id2][id1] =  res

    pickle.dump(relatedness_cache, open('/home/vprovat/EL_pickles/relatedness_cache.p', 'wb'))
    return res

def entity_mention_distance(entity, mention):
    return 1

def make_graph(mentions):
    entity_nodes = []
    mention_nodes = []
    # Step 1: edges between mentions and entities (candidates) for relevance
    for entry in mentions:
        mention_node = MentionNode(entry.mention)  # mention
        for cand in entry.candidates:
            mention_node.add_edge(target_name=cand.candidate, weight=cand.score)
            cand_node = EntityNode(cand.candidate)
            cand_node.add_edge(target_name=entry.mention, weight=cand.score, mention_edge=True)
            entity_nodes.append(cand_node)
        mention_nodes.append(mention_node)

    # Step 2: edges between entities for coherence
    for i, ent_1 in enumerate(tqdm(entity_nodes)):
        for ent_2 in entity_nodes[i + 1:]:
            rel_weight = relatedness(ent_1, ent_2)
            ent_1.add_edge(ent_2.name, weight=rel_weight, mention_edge=False)
            ent_2.add_edge(ent_1.name, weight=rel_weight, mention_edge=False)

    return mention_nodes, entity_nodes

if __name__ == '__main__':
    PATH_TO_ENTRIES = '/home/vprovat/EL_pickles/entries_shadow_REL_ner_no_threshold.p'
    entries = pickle.load(open(PATH_TO_ENTRIES, 'rb'))

    PATH_TO_ANSWERS = '/home/vprovat/EL_pickles/res_shadow_AIDA_v0.p'
    try:
        res = pickle.load(open(PATH_TO_ANSWERS, 'rb'))
    except:
        res = []
    cur_len = len(res)

    for item in tqdm(entries[cur_len:]):
        # print(item)
        mention_nodes, entity_nodes = make_graph(item)
        # for node in mention_nodes:
        #     node.display()
        # for node in entity_nodes:
        #     node.display()

        res_mention, res_entity = disambiguate(mention_nodes, entity_nodes)
        answer = []
        for node in res_mention:
            final_cand = list(node.edges.keys())[0] # first and only candidate left
            answer.append(MentionEntry(node.name, final_cand))

        res.append(answer)
        if len(res) % 3 == 0:
            print(answer)
            pickle.dump(res, open(PATH_TO_ANSWERS, 'wb'))


