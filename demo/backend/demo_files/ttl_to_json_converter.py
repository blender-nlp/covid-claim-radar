"""TTL to JSON converter.

You will need to additionally install the following:
* aida_interchange==1.2.2
* rdflib
"""

import argparse
import json
from collections import defaultdict
from typing import Dict, List, Any, Tuple, Optional, Union

import rdflib.term
from aida_interchange import aifutils
from aida_interchange.rdf_ontologies import interchange_ontology
from pathlib import Path

from attr import attrs, attrib
from rdflib import RDF, Graph, Namespace, URIRef
from rdflib.plugins.sparql import prepareQuery
from rdflib.term import Node

MISSING = "MISSING"

# Todo: Not letting me query with aida namespace; figure out alternative
# (This one doesn't work as intended)
_ARG_QUERY = prepareQuery("""SELECT ?argAssertion WHERE {
  ?argAssertion a rdf:Statement .
  ?argAssertion rdf:subject ?argObject .
  }
  """)


@attrs
class Entity(object):
    """Representation of an Entity or Event."""
    entity_id: str = attrib()
    source: str = attrib()
    confidence: float = attrib()
    justifications: Dict[str, List[Tuple[int, int]]] = attrib()
    text: str = attrib()
    start: int = attrib()
    end: int = attrib()
    ke: List[List[str]] = attrib()
    identity_qnode: Optional[str] = attrib()
    type_qnode: str = attrib()
    arguments: Dict[str, Any] = attrib()


@attrs
class Component(object):
    """Representation of a Claimer or XVariable."""
    component_start: int = attrib()
    component_end: int = attrib()
    component_debug: Dict[str, Any] = attrib()
    component_ke: List[Any] = attrib()
    component_ke_typeqnode: List[str] = attrib()
    component_ke_qnode: List[str] = attrib()
    component_text: str = attrib()
    component_score: float = attrib()
    component_qnode: str = attrib()
    component_type_qnode: str = attrib()


class Claim(object):
    """A claim to be represented in JSON."""
    sentence: str = MISSING
    claim_span_text: str = MISSING
    claimbuster_score: float = 0.0
    claimer_end: int = 0
    start_char: int = 0
    time_end_earliest: Optional[Dict[str, Any]]
    claimer_debug: Dict[str, Any]
    associated_KEs: List[Any]
    claimer_ke: List[Any]  # ?
    claim_span_end: int = 0
    claim_id: str
    x_ke_typeqnode: List[str]
    claim_span_start: int = 0
    equivalent_claims: List[str]
    time_end_latest: Optional[Dict[str, Any]]
    x_end: int = 0
    claimer_start: int = 0
    end_char: int = 0
    refuting_claims: List[str]
    time_start_earliest: Optional[Dict[str, Any]]
    location: Optional[str]
    template: str = MISSING
    final_claim_score: float = 0.0
    claimer_ke_typeqnode: List[str]
    x_start: int = 0
    stance: str = "unknown"
    x_ke: List[str]
    news_author: str = ""
    claim_semantics: List[Any]
    topic_score: float = 0.0
    time_start_latest: Optional[Dict[str, Any]]
    claimer_ke_qnode: List[str]
    topic: str = MISSING
    claimer_text: str = "<AUTHOR>"
    segment_id: str = MISSING
    x_variable: str = MISSING
    claimer_score: float = 0.0
    claimer_qnode: str = MISSING
    qnode_x_variable_identity: str = MISSING
    qnode_x_variable_type: str = MISSING
    x_ke_qnode: List[str]
    claimer_type_qnode: str = MISSING
    sub_topic: str = MISSING
    supporting_claims: List[str]
    news_url: str = MISSING

    @staticmethod
    def _get_confidence(confidence_node: Node, graph: Graph, aida: Namespace) -> float:
        """Get confidence values given an aida:Confidence.

        If there is no confidence value, return 1.0.
        """
        return graph.value(subject=confidence_node, predicate=aida.confidenceValue) or 1.0

    @staticmethod
    def _get_offsets_from_justification(
            justification: Node, graph: Graph, aida: Namespace
    ) -> Tuple[int, int]:
        """Get span offsets given a justification node."""
        start = graph.value(subject=justification, predicate=aida.startOffset) or -1
        end = graph.value(subject=justification, predicate=aida.endOffsetInclusive) or -1
        return start, end

    @staticmethod
    def _get_argument_statements(graph: Graph, subject: Node):
        """Retrieve all argument assertions from an entity."""
        query_result = graph.query(_ARG_QUERY, initBindings={'argObject': subject})
        return [x for (x,) in query_result]

    def _entity(
            self,
            entity: Node,
            graph: Graph,
            aida: Namespace,
            entity_cluster: Optional[Node] = None
    ) -> Entity:
        """Extract entity data given an aida:Entity node."""
        uri = str(entity_cluster) if entity_cluster else str(entity)
        entity_id = uri.split("/")[-1]
        text = (
                   graph.value(subject=entity, predicate=aida.hasName) or
                   graph.value(subject=entity, predicate=aida.textValue) or
                   graph.value(subject=entity, predicate=aida.handle)
        )
        confidence = self._get_confidence(
            graph.value(subject=entity, predicate=aida.confidence), graph, aida
        )

        # Justifications
        informative_justification = graph.value(
            subject=entity, predicate=aida.informativeJustification
        )
        start, end = self._get_offsets_from_justification(
            informative_justification, graph, aida
        )
        source = graph.value(subject=informative_justification, predicate=aida.source)
        all_justifications = defaultdict(list)
        justified_by = graph.objects(subject=entity, predicate=aida.justifiedBy)
        for justification in justified_by:
            j_start, j_end = self._get_offsets_from_justification(justification, graph, aida)
            j_source = graph.value(subject=justification, predicate=aida.source)
            all_justifications[j_source].append((j_start, j_end))

        link = graph.value(subject=entity, predicate=aida.link)
        identity_qnode = graph.value(
            subject=link, predicate=aida.linkTarget
        ) if link else None

        # Get Entity/Event type
        type_assertions = aifutils.get_type_assertions(graph, URIRef(str(entity)))
        if type_assertions:
            type_qnode = graph.value(subject=type_assertions[0], predicate=RDF.object)
        else:
            type_qnode = MISSING

        # There is also supposed to be a role label in this list,
        # but I'm not sure where to extract that from
        ke = [entity_id]
        if text:
            ke.append(text)
        ke.extend([f"{source}:{start}-{end}", uri])

        # Get arguments if it is an event or relation
        argument_dict = {}
        argument_statements = self._get_argument_statements(graph, entity)
        for argument_statement in argument_statements:
            role = graph.value(subject=argument_statement, predicate=RDF.predicate)
            if type(role) != rdflib.term.Literal:  # hack for bad argument query
                continue
            argument_entity_node = graph.value(
                subject=argument_statement, predicate=RDF.object
            )
            argument_entity = self._entity(argument_entity_node, graph, aida)
            argument_data_list: List[Union[str, float]] = [
                f"{source}:{start}-{end}"
                for source, offset_list in argument_entity.justifications.items()
                for start, end in offset_list
            ]
            argument_data_list.append(argument_entity.confidence)
            argument_dict[role] = {
                argument_entity.entity_id: argument_data_list
            }

        if argument_dict:
            ke.append(argument_dict)

        return Entity(
            entity_id=entity_id,
            source=source,
            confidence=confidence,
            justifications=all_justifications,
            text=text,
            start=start,
            end=end,
            ke=ke,
            identity_qnode=identity_qnode,
            type_qnode=type_qnode,
            arguments=argument_dict
        )

    def _component(self, component: Node, graph: Graph, aida: Namespace) -> Component:
        """Return data related to the claimer or x-variable."""
        identity_qnode = graph.value(subject=component, predicate=aida.componentIdentity)
        type_qnode = graph.value(subject=component, predicate=aida.componentType)
        text = graph.value(subject=component, predicate=aida.componentName)
        component_ke_node = graph.value(subject=component, predicate=aida.componentKE)
        if component_ke_node:
            component_entity = self._entity(component_ke_node, graph, aida)
            component_score = component_entity.confidence
            component_start = component_entity.start
            component_end = component_entity.end
            component_ke = component_entity.ke
            component_ke_typeqnode = [component_entity.type_qnode]  # leavings these as todo for now
            component_ke_qnode = [component_entity.identity_qnode]
        else:
            component_start, component_end = -1, -1
            component_ke = []
            component_ke_typeqnode = [type_qnode]
            component_ke_qnode = [identity_qnode]
            component_score = 1.0
        return Component(
            component_start=component_start,
            component_end=component_end,
            component_debug={},
            component_ke=component_ke,
            component_ke_typeqnode=component_ke_typeqnode,
            component_ke_qnode=component_ke_qnode,
            component_text=text,
            component_score=component_score,
            component_qnode=identity_qnode,
            component_type_qnode=type_qnode
        )

    def as_dict(self, claim: Node, graph: Graph, aida: Namespace) -> Dict[str, Any]:
        """Return the claim data as a JSON serializable."""
        all_type_statements = list(graph.subjects(predicate=RDF.type, object=aida.TypeStatment))
        type_dict = {}
        for statement in all_type_statements:
            entity = graph.value(subject=statement, predicate=RDF.subject)
            entity_type = graph.value(subject=statement, predicate=RDF.object)
            type_dict[entity] = entity_type
        # Sentence field is missing
        self.sentence = MISSING
        self.start_char = -1
        self.end_char = -1

        # Surface-level claim data
        self.claim_id = graph.value(subject=claim, predicate=aida.claimId)
        self.segment_id = MISSING
        self.claim_span_text: str = graph.value(
            subject=claim, predicate=aida.naturalLanguageDescription
        )
        self.template: str = graph.value(
            subject=claim, predicate=aida.claimTemplate
        )
        self.topic = graph.value(subject=claim, predicate=aida.topic)
        self.sub_topic = graph.value(subject=claim, predicate=aida.subtopic)
        self.topic_score = 0.0  # missing

        epistemic = graph.value(subject=claim, predicate=aida.epistemic)
        if epistemic in {aida.EpistemicTrueCertain, aida.EpistemicTrueUncertain}:
            self.stance = "affirm"
        elif epistemic in {aida.EpistemicFalseCertain, aida.EpistemicFalseUncertain}:
            self.stance = "refute"
        else:
            self.stance = "unknown"  # ??

        # Not sure what claimbuster score is, but assuming it's aida:importance
        self.claimbuster_score: float = graph.value(
            subject=claim, predicate=aida.importance
        )
        # Get claim justification data
        claim_justification = graph.value(subject=claim, predicate=aida.justifiedBy)
        self.claim_span_start, self.claim_span_end = self._get_offsets_from_justification(
            claim_justification, graph, aida
        )
        self.final_claim_score = self._get_confidence(
            graph.value(subject=claim_justification, predicate=aida.confidence),
            graph,
            aida
        )
        source = graph.value(subject=claim_justification, predicate=aida.source)

        # Get data for claimer
        claimer_node = graph.value(subject=claim, predicate=aida.claimer)
        claimer = self._component(claimer_node, graph, aida)
        self.claimer_start: int = claimer.component_start
        self.claimer_end: int = claimer.component_end
        self.claimer_debug = claimer.component_debug
        self.claimer_text = claimer.component_text
        self.claimer_score = claimer.component_score
        self.claimer_ke = claimer.component_ke
        self.claimer_ke_qnode = claimer.component_ke_qnode
        self.claimer_ke_typeqnode = claimer.component_ke_typeqnode
        self.claimer_qnode = claimer.component_qnode
        self.claimer_type_qnode = claimer.component_type_qnode

        # Get data for x-variable
        x_variable_node = graph.value(subject=claim, predicate=aida.xVariable)
        x_variable = self._component(x_variable_node, graph, aida)
        self.x_variable = x_variable.component_text
        self.x_start = x_variable.component_start
        self.x_end = x_variable.component_end
        self.qnode_x_variable_identity = x_variable.component_qnode
        self.qnode_x_variable_type = x_variable.component_type_qnode
        self.x_ke = x_variable.component_ke
        self.x_ke_typeqnode = x_variable.component_ke_typeqnode
        self.x_ke_qnode = x_variable.component_ke_qnode

        # Get time/location data (todo)
        # self.time_end_earliest = MISSING
        # self.time_end_latest = MISSING
        # self.time_start_earliest = MISSING
        # self.time_start_lastest = MISSING
        # self.location = MISSING

        # Associated KEs and claim semantics
        associated_kes = []
        associated_ke_clusters = list(graph.objects(subject=claim, predicate=aida.associatedKEs))
        for ke_cluster in associated_ke_clusters:
            associated_ke = graph.value(subject=ke_cluster, predicate=aida.prototype)
            associated_kes.append(
                self._entity(associated_ke, graph, aida, ke_cluster).ke
            )
        self.associated_KEs = associated_kes
        claim_semantics = []
        claim_semantics_clusters = list(graph.objects(subject=claim, predicate=aida.claimSemantics))
        for semantics_cluster in claim_semantics_clusters:
            claim_semantics_node = graph.value(subject=semantics_cluster, predicate=aida.prototype)
            claim_semantics.append(
                self._entity(claim_semantics_node, graph, aida).ke
            )
        self.claim_semantics = claim_semantics

        # Relevant claims
        self.equivalent_claims = [MISSING]
        self.refuting_claims = [MISSING]
        self.supporting_claims = [MISSING]

        # Not sure where news_author is
        self.news_author = MISSING
        self.news_url = MISSING

        return vars(self)


def main(input_dir: Path, output_json: Path):
    """TTL to JSON converter.

    Unknown fields:
    ---------------
    * sentence + its offsets
    * claimbuster_score (though I think it's aida:importance)
    * segment_id
    * claimer_debug
    * topic_score
    * equivalent_claims
    * refuting_claims
    * supporting_claims

    Uncertain fields:
    -----------------
    * labels for events; could try extracting from uri, but feels hacky
    """
    # Convert by document/claim
    all_claims_dict: Dict[str, List[Any]] = defaultdict(list)
    for input_file in input_dir.iterdir():
        if input_file.suffix == ".ttl":
            graph = Graph()
            graph.parse(source=str(input_file), format="turtle")
            aida = aida_namespace(graph)

            # There should be one claim per doc
            claim_node = list(graph.subjects(predicate=RDF.type, object=aida.Claim))[0]

            claim_id: str = graph.value(subject=claim_node, predicate=aida.claimId)
            # A 'source' field is missing from the ttl;
            # for now just extract from the claim ID.
            # Format: claim_<docID>_#
            claim_source = claim_id.split("_")[1]

            # Add Claim to the list
            claim = Claim().as_dict(claim_node, graph, aida)
            all_claims_dict[claim_source].append(claim)

    with open(output_json, 'w', encoding="utf-8") as out_json:
        json.dump(all_claims_dict, out_json, indent=4)

    print("Done!")


def aida_namespace(graph: Graph) -> Namespace:
    try:
        aida = Namespace(dict(graph.namespace_manager.namespaces())["aida"])
    except KeyError:
        aida = interchange_ontology

    return aida


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ttl_dir", help="Path to the source ttl", type=Path)
    parser.add_argument("json_file", help="Path to the output json file", type=Path)
    args = parser.parse_args()
    main(args.ttl_dir, args.json_file)
