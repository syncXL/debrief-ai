from typing import Literal
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field



class ExtractNodes(MessagesState):
    context : str
    tool_caller : str

class ExtractRels(MessagesState):
    nodes : str
    context : str
    tool_caller : str

class FlexibleExtra(BaseModel):
    """
    Key-value store for label-specific or relationship-specific properties.
    Uses parallel lists to satisfy OpenAI structured output requirements
    (additionalProperties: false on all object schemas).

    Populate only from what the article explicitly states.
    Complex values (lists, numbers) should be serialised to JSON strings.

    Node examples:
      Role/Position:        keys=['title','holder','jurisdiction']
                            values=['Governor','Olayemi Cardoso','Nigeria']
      Economic Indicator:   keys=['value','unit','currency']
                            values=['27.5','percent','null']
      Location:             keys=['locationType','country','coordinates']
                            values=['city','Nigeria','[6.5244, 3.3792]']

    Relationship examples:
      OWNS_STAKE:           keys=['percentage','acquisitionDate','currency']
                            values=['22.5','2021-04-01','NGN']
      FINED:                keys=['amount','currency','reason']
                            values=['220000000','NGN','forex violations']
    """
    model_config = {"extra": "forbid"}

    keys: list[str] = Field(
        default_factory=list,
        description="Property names. Must be camelCase. Parallel to `values`."
    )
    values: list[str] = Field(
        default_factory=list,
        description=(
            "Property values as strings. Parallel to `keys`. "
            "Serialise numbers and booleans as strings (e.g. '27.5', 'true'). "
            "Serialise lists as JSON arrays (e.g. '[6.5244, 3.3792]'). "
            "Use 'null' for explicitly absent values."
        )
    )


class NodeProperties(BaseModel):
    """
    Single flattened properties model for all node types.
    Which fields are relevant depends on the temporalTier and labels on the parent Node.

    Core fields are always required.
    Temporal fields are required for TEMPORAL tier, optional otherwise.
    Extra carries label-specific properties for any tier.
    """
    model_config = {"extra": "forbid"}

    # ── Core (always required) ───────────────────────────────────────────────
    name: str = Field(
        description="Primary name of the entity as stated in the source article."
    )
    aliases: list[str] = Field(
        default_factory=list,
        description=(
            "Alternative names, abbreviations, or former names. "
            "E.g. ['CBN', 'Central Bank'] for 'Central Bank of Nigeria'."
        )
    )
    sourceUrls: list[str] = Field(
        description="URLs of the articles this entity was first extracted from. At least one required."
    )

    # ── Temporal (required for TEMPORAL tier, optional for CONDITIONAL_TEMPORAL) ─
    validFrom: str | None = Field(
        default=None,
        description=(
            "ISO date when this state became true per source article. E.g. '2023-06-01'. "
            "Required for TEMPORAL tier nodes. "
            "Optional for CONDITIONAL_TEMPORAL — populate if the article states it. "
            "Always null for PERMANENT tier."
        )
    )
    validUntil: str | None = Field(
        default=None,
        description=(
            "ISO date when this state ended. "
            "Always null at creation. "
            "Only set by a subsequent pass when a source article explicitly states the end of this state. "
            "Never infer this from context."
        )
    )

    # ── Extra (label-specific, any tier) ─────────────────────────────────────
    extra: FlexibleExtra = Field(
        default_factory=FlexibleExtra,
        description=(
            "Label-specific properties that do not belong in the core schema. "
            "Only populate from what the article explicitly states. "
            "Never add properties that should be relationships "
            "(employment, education, ownership stake → use relationships instead). "
            "\n"
            "TEMPORAL examples:\n"
            "  Role/Position:       keys=['title','holder','jurisdiction']\n"
            "                       values=['Governor','Olayemi Cardoso','Nigeria']\n"
            "  Policy/Law:          keys=['jurisdiction','status']\n"
            "                       values=['Federal Republic of Nigeria','enacted']\n"
            "  Economic Indicator:  keys=['value','unit','currency','jurisdiction']\n"
            "                       values=['27.5','percent','null','Ghana']\n"
            "  Sanction/Restriction:keys=['target','issuer','reason']\n"
            "                       values=['Entity name','Issuing body','Stated reason']\n"
            "  Alliance/Coalition:  keys=['members','purpose']\n"
            "                       values=['[\"Party A\",\"Party B\"]','Stated purpose']\n"
            "  Conflict/Crisis:     keys=['conflictType','location']\n"
            "                       values=['trade_dispute','Red Sea']\n"
            "\n"
            "CONDITIONAL_TEMPORAL examples:\n"
            "  Person:              keys=['nationality','birthDate']\n"
            "                       values=['Nigerian','1952-03-29']\n"
            "  Organisation:        keys=['orgType','sector']\n"
            "                       values=['commercial_bank','financial_services']\n"
            "  Government Body:     keys=['bodyType','jurisdiction']\n"
            "                       values=['regulatory_agency','Nigeria']\n"
            "  Product/Technology:  keys=['creator','category']\n"
            "                       values=['Organisation name','mobile_payments']\n"
            "  Project/Initiative:  keys=['initiator','scope']\n"
            "                       values=['Entity name','national']\n"
            "  Financial Instrument:keys=['amount','currency','status','instrumentType']\n"
            "                       values=['50000000000','NGN','active','bond']\n"
            "\n"
            "PERMANENT examples:\n"
            "  Location:            keys=['locationType','country','coordinates']\n"
            "                       values=['city','Nigeria','[6.5244,3.3792]']\n"
            "  EventInstance:       keys=['eventType','date','location','outcome']\n"
            "                       values=['election','2023-02-25','Nigeria','Tinubu declared winner']\n"
            "  EventSeries:         keys=['cadence','governingBody']\n"
            "                       values=['quadrennial','INEC']\n"
            "  Concept/Ideology:    keys=['category']\n"
            "                       values=['economic_policy']\n"
            "  Natural Resource:    keys=['resourceType','location']\n"
            "                       values=['crude_oil','Niger Delta']"
        )
    )


# ─── Node ────────────────────────────────────────────────────────────────────

class Node(BaseModel):
    model_config = {"extra": "forbid"}

    action: Literal["create", "update"] = Field(
        description=(
            "'create' if this is a new node not found in the graph. "
            "'update' if an existing node was matched and requires changes such as new aliases."
        )
    )
    resolvedId: str | None = Field(
        default=None,
        description=(
            "Neo4j elementId of the matched node. "
            "Null on create — Neo4j assigns the ID on write. "
            "Must be populated on update. E.g. '4:abc123:0'."
        )
    )
    labels: list[str] = Field(
        max_length=4,
        description=(
            "List of labels for this node. Max 4. "
            "Always includes the specific type label and the temporal tier label. "
            "E.g. ['Person', 'ConditionalTemporal'], ['Policy', 'Temporal'], ['Location', 'Permanent']. "
            "New labels must be generalised — 'Legislator' not 'NigerianSenator'. "
            "'OilCompany' is rejected in favour of 'Organisation' with extra keys orgType='oil_company'. "
            "Do not encode property values in label names."
        )
    )
    temporalTier: Literal["Temporal", "ConditionalTemporal", "Permanent"]
    properties: NodeProperties = Field(
        description="Properties for this node. Populate only from what the article explicitly states."
    )
    confidence: float = Field(
        ge=0.5,
        le=1.0,
        description=(
            "Confidence this entity is correctly identified and typed. "
            "Score on three factors: "
            "entity is explicitly named in article (0.3), "
            "entity type is unambiguous (0.4), "
            "properties can be populated without inference (0.3). "
            "Nodes below 0.5 must not be submitted — they belong in discarded."
        )
    )
    suggestedMerge: bool = Field(
        default=False,
        description=(
            "True if this node was matched via fuzzy name similarity above 0.85 but not exact. "
            "Flags the match for review. The node is still used — do not create a duplicate."
        )
    )
    newLabelJustification: str | None = Field(
        default=None,
        description=(
            "Required if any label in `labels` does not exist in the current graph schema. "
            "Must state: (1) which existing labels were considered and rejected, "
            "(2) why none fit without losing critical information, "
            "(3) why this new label name is general enough to apply to future entities beyond this one. "
            "E.g. 'Considered Organisation — rejected because this entity is a supranational body "
            "with treaty-based authority and no commercial mandate. "
            "RegionalBody fits future entities like ECOWAS Commission, AU, OPEC Secretariat.'"
        )
    )


class RelationshipProperties(BaseModel):
    model_config = {"extra": "forbid"}

    context: str = Field(
        description=(
            "1-2 sentences describing the specific nature of this connection, "
            "drawn directly from the article text. Must name both entities and state what happened. "
            "Rejected: 'Entity A is connected to Entity B.' "
            "Accepted: 'The SEC mandated the Central Securities Clearing System in March 2024 "
            "to implement a T+1 settlement window for all NGX equities, reducing counterparty risk.'"
        )
    )
    sourceUrls: list[str] = Field(
        description="URLs of articles supporting this relationship. At least one required."
    )
    validFrom: str = Field(
        description="ISO date when this relationship became true per source article."
    )
    validUntil: str | None = Field(
        default=None,
        description=(
            "ISO date when this relationship ended. "
            "Always null at creation. "
            "Only set when a source article explicitly states the relationship has ended."
        )
    )
    extra: FlexibleExtra = Field(
        default_factory=FlexibleExtra,
        description=(
            "Quantitative or qualifying properties specific to this relationship type. "
            "Only populate from what the article explicitly states. "
            "\n"
            "OWNS_STAKE:      keys=['percentage','acquisitionDate','currency']\n"
            "                 values=['22.5','2021-04-01','NGN']\n"
            "INVESTED_IN:     keys=['amount','currency','instrumentType']\n"
            "                 values=['500000000','USD','equity']\n"
            "HOLDS_POSITION:  keys=['title','appointingBody']\n"
            "                 values=['Managing Director','Board of Directors']\n"
            "PARTICIPATED_IN: keys=['role','outcome']\n"
            "                 values=['host nation','qualified for round of 16']\n"
            "FINED:           keys=['amount','currency','reason']\n"
            "                 values=['220000000','NGN','forex violations']\n"
            "RECEIVED_AID:    keys=['amount','currency','donor','purpose']\n"
            "                 values=['1200000000','USD','IMF','balance of payments support']\n"
            "AWARDED:         keys=['value','currency','scope','date']\n"
            "                 values=['45000000','USD','pipeline construction','2024-11-01']\n"
            "ACCUSED_OF:      keys=['allegation','accuser','caseStatus']\n"
            "                 values=['money laundering','EFCC','under investigation']\n"
            "IN_CONFLICT_WITH:keys=['conflictType','intensity','startDate']\n"
            "                 values=['territorial_dispute','low','2023-01-01']"
        )
    )


class Relationship(BaseModel):
    model_config = {"extra": "forbid"}

    action: Literal["create", "update_urls"] = Field(
        description=(
            "'create' for a new relationship not found in the graph. "
            "'update_urls' if this relationship already exists and is still active — "
            "only appends the new sourceUrl, nothing else is changed."
        )
    )
    fromNodeId: str = Field(
        description=(
            "Neo4j elementId of the source node. "
            "Must be a resolved ID returned from the node pass. "
            "E.g. '4:abc123:0'."
        )
    )
    toNodeId: str = Field(
        description=(
            "Neo4j elementId of the target node. "
            "Must be a resolved ID returned from the node pass. "
            "E.g. '4:def456:1'."
        )
    )
    type: str = Field(
        description=(
            "Relationship type in ALL_CAPS_UNDERSCORE format. "
            "Use an existing type if one fits — always prefer existing over new. "
            "Existing types: HOLDS_POSITION, EMPLOYED_BY, OWNS_STAKE, INVESTED_IN, "
            "PARTICIPATED_IN, INSTANCE_OF, SANCTIONED_BY, IN_CONFLICT_WITH, ACCUSED_OF, "
            "CAUSED, RESPONDED_TO, SUPERSEDED_BY, REPRESENTS, ATTENDED, MERGED_WITH, "
            "AWARDED, RECEIVED_AID, HOSTED, REGULATES, FINED."
        )
    )
    properties: RelationshipProperties = Field(
        description="Mandatory properties for this relationship. All fields required except validUntil and extra."
    )
    confidence: float = Field(
        ge=0.7,
        le=1.0,
        description=(
            "Confidence this relationship is correctly identified and directed. "
            "Score on three factors: "
            "article explicitly states the connection (0.4), "
            "direction is unambiguous (0.3), "
            "context can be written without inference (0.3). "
            "Relationships below 0.7 must not be submitted — they belong in discarded."
        )
    )
    newTypeJustification: str | None = Field(
        default=None,
        description=(
            "Required if `type` does not exist in the current graph schema. "
            "Must state: (1) which existing types were considered and rejected, "
            "(2) why none fit, "
            "(3) why this new type name is general enough to apply across many entity pairs. "
            "E.g. 'Considered CAUSED and RESPONDED_TO — rejected because this describes "
            "a formal consolidation. MERGED_WITH applies to any two organisations "
            "undergoing a formal merger regardless of sector.'"
        )
    )



class Output(BaseModel):
    model_config = {"extra": "forbid"}

    nodes: list[Node] = Field(
        description="All nodes to create or update from this article pass."
    )
    relationships: list[Relationship] = Field(
        description=(
            "All relationships to create or update. "
            "Every fromNodeId and toNodeId must appear in the nodes list above "
            "or be a pre-existing resolved ID from the graph."
        )
    )
    discarded: list[str] = Field(
        default_factory=list,
        description=(
            "Entities or relationships considered but dropped due to low confidence or insufficient evidence. "
            "Each entry is a reason string for logging only — nothing is written to the graph. "
            "E.g. 'Dropped EMPLOYED_BY between Adeyemi and Zenith Bank — confidence 0.55, "
            "article mentions attendance at bank event but does not state employment.'"
        )
    )

class Archiver(MessagesState):
    nodes : str
    relationships : str
    full_knowledge : Output
    tool_caller : str
