# Research Report: Nancy Leveson's Intent Specifications

## Sources used

Primary sources read in full or in the relevant part:

- Leveson, "Intent Specifications: An Approach to Building Human-Centered Specifications", IEEE TSE 26(1), Jan 2000, pp. 15-35. http://sunnyday.mit.edu/papers/intent-tse.pdf
- Leveson and Reese, TCAS II Intent Specification (805 pages, dated 6 Aug 1999). http://sunnyday.mit.edu/tcas-intent.pdf
- Leveson, *Engineering a Safer World* (ESW), MIT Press 2011, chapter 10 "Integrating Safety into System Engineering", section 10.2 "Intent Specifications" (pp. 309-313) and the TCAS worked example (pp. 328-346). Open access: https://direct.mit.edu/books/oa-monograph-pdf/2280500/book_9780262298247.pdf (mirror: https://www.flighttestsafety.org/images/Engineering_a_Safer_World.pdf)
- Leveson, "Final Report: Intent Specifications", NASA grant NAG-1-1495, 1999. https://ntrs.nasa.gov/api/citations/19990089302/downloads/19990089302.pdf
- Stringfellow Herring, Owens, Leveson, Ingham, Weiss, "Safety-Driven Model-Based System Engineering Methodology Part I", MIT/JPL, Dec 2007. http://sunnyday.mit.edu/JPL-Part-1.pdf
- Weiss, Ong, Leveson, "Reusable Specification Components for Model-Driven Development" (INCOSE). http://sunnyday.mit.edu/papers/incose.pdf
- Weiss, Ong, Leveson, "Reusable Software Architectures for Aerospace Systems". http://sunnyday.mit.edu/nasa-class/components.pdf
- Weiss, Dulac, Chiesi, Daouk, Zipkin, Leveson, "Engineering Spacecraft Mission Software using a Model-Based and Safety-Driven Design Methodology", J. Aerospace Computing, Information, and Communication 3, Nov 2006. http://sunnyday.mit.edu/AIAA-Weiss.pdf
- Navarro, Leveson, Lundqvist, "Reducing the Effects of Requirements Changes through System Design". http://sunnyday.mit.edu/papers/coupling.pdf
- FAA, "Requirements Engineering Management Findings Report", DOT/FAA/AR-08-34, 2009. https://www.faa.gov/sites/faa.gov/files/aircraft/air_cert/design_approvals/air_software/AR-08-34.pdf
- Mohan, "Architecting Safe Automated Driving with Legacy Platforms", KTH licentiate thesis 2018. https://arxiv.org/abs/2001.02496

Two caveats on method. The host sunnyday.mit.edu refused connections from this machine, so the MIT PDFs were retrieved from the Wayback Machine (web.archive.org). The TCAS PDF uses Type 3 fonts that defeat text extraction, so its pages were read as rendered images (preface pp. i-iii, pp. 3, 19, 29, 33, 59, 139, 239, 509). The SpecTRM tutorial PDF at sunnyday.mit.edu/16.863/SpecTRM-tutorial.pdf is not in the archive. Safeware Engineering's own SpecTRM manuals are no longer online.

## 1. Level structure, and how it changed between 2000 and 2011

The 2000 TSE paper defines **five** intent levels. Work from MIT from about 2003 onward (Weiss/Ong INCOSE paper, JPL 2007 report) and ESW (2011) define **seven** levels, adding a Level 0 above and a Level 6 below. The five original levels kept their numbers and, with one renaming, their names.

| Level | TSE 2000 name | ESW 2011 name and "view" (Fig. 10.1) | Content |
|---|---|---|---|
| 0 | (absent) | Program Management (Management View) | "project management plans, the safety plan, status information, and so on" (ESW p. 311). JPL 2007 also places accidents / unacceptable losses (ACC1...) and customer programmatic constraints (PC1) here. |
| 1 | System Purpose | System Purpose (Customer View) | "system goals, design constraints, assumptions, limitations, design evaluation criteria and priorities, and results of analyses for system level qualities" (TSE 4.2.1). ESW adds "definitions of accidents, hazard information". Constraints are split into safety-related (SC) and other (C). Operator requirements (OP), environment assumptions (EA), environment constraints (EC), limitations (L), and the hazard analysis (fault tree in 1999; STPA in ESW) live here. |
| 2 | System Design Principles | System Design Principles (System Engineering View) | "the basic system design and scientific and engineering principles needed to achieve the behavior specified in the top level" (TSE 4.2.2), "as well as any derived requirements and design features not related to the level 1 requirements" (ESW p. 338). Tradeoffs and assumptions are recorded here. |
| 3 | Blackbox Behavior | System Architecture (Interface between System and Component Engineers). ESW Fig. 10.2 labels the row "Blackbox Models". | "specifies the system components and their interfaces, including the human components (operators)" (TSE 4.2.3). Environment component models (with failure modes), operator task models, HCI models, formal blackbox behavioural models in SpecTRM-RL, interface specifications, testing requirements. "Purely blackbox: They describe the inputs and outputs of each component ... only in terms of externally visible variables." |
| 4 | Design Representation | Design Representation (Component Designer View) | "the first place where the specification should include information about the physical or logical implementation of the components." Software and hardware design specs, HCI design. For TCAS, "simply contains the official pseudocode design specification" from MITRE. |
| 5 | Physical Representation | Physical Representation (Component Implementer View) | "the software itself, hardware assembly instructions, training requirements (plan), etc." ESW: software code, hardware assembly instructions, GUI and physical controls design. |
| 6 | (absent) | System Operations (Operations View) | "a view of the operational system and acts as the interface between development and operations ... required or suggested operational audit procedures, user manuals, training materials, maintenance requirements, error reports and change requests, historical usage information" (ESW p. 313). |

One knock-on effect of adding Level 6: the TSE paper puts the "Pilot Operations (Flight) Manual on Level 4 of our TCAS intent specification", whereas ESW routes the same pointer to "Aircraft Flight Manual on level 6" and points assumption audits to "↓ 6.17".

The 1999 TCAS document's table of contents (TSE Fig. 3) uses slightly different chapter titles than the level names:

```
1. System Purpose
   1.1 Introduction  1.2 Historical Perspective
   1.3 Environment (1.3.1 Environmental Assumptions, 1.3.2 Environmental Constraints)
   1.4 Operator (1.4.1 Tasks and Procedures, 1.4.2 Pilot-TCAS Interface Requirements)
   1.5 TCAS System Goals  1.6 High-Level Functional Requirements
   1.7 System Limitations
   1.8 System Constraints (1.8.1 General Constraints, 1.8.2 Safety-Related Constraints)
   1.9 Hazard Analysis
2. System Design Principles
   2.1 General Description  2.2 TCAS System Components
   2.3 Surveillance and Collision Avoidance Logic (2.3.1-2.3.6: General Concepts,
       Surveillance, Tracking, Traffic Advisories, Resolution Advisories, TCAS/TCAS Coordination)
   2.4 Performance Monitoring  2.5 Pilot-TCAS Interface (Controls; Displays and Aural Annunciations)
   2.6 Testing and Validation (Simulations, Experiments, Other Validation Procedures and Results)
3. Blackbox Behavior
   3.1 Environment  3.2 Flight Crew Requirements (Tasks, Operational Procedures)
   3.3 Communication and Interfaces (Pilot-TCAS Interface, Message Formats, Input Interfaces,
       Output Interfaces, Receiver/Transmitter/Antennas)
   3.4 Behavioral Requirements (Surveillance, Collision Avoidance, Performance Monitoring)
   3.5 Testing Requirements
4. Physical and Logical Function
   4.1 Human-Computer Interface Design  4.2 Pilot Operations (Flight) Manual  4.3 Software Design
   4.4 Physical Requirements (4.4.1-4.4.11: standard conditions, Mode S transponder capability,
       receiver, transmitter, pulse, decoder characteristics, interference limiting, suppression bus,
       data handling, bearing estimation, high-density techniques)
   4.5 Hardware Design Specifications  4.6 Verification Requirements
5. Physical Realization
   5.1 Software  5.2 Hardware Assembly Instructions  5.3 Training Requirements (Plan)
   5.4 Maintenance Requirements
Appendices A-H: Constant Definitions, Table Definitions, Reference Algorithms,
   Physical Measurement Conventions, Performance Requirements on Equipment that Interacts
   with TCAS, Glossary, Notation Guide, Index
```

Leveson notes that only Level 1 and Level 2 were written by her for the intent-spec experiment, Jon Reese rewrote the Level 3 logic into SpecTRM-RL, and Level 4 is imported pseudocode (ESW footnote 7, p. 344).

### TCAS II example content at each level

Level 1 (TSE 4.2.1; TCAS spec p. 19, 29, 33; ESW pp. 328-338):

```
[G.1] Provide affordable and compatible collision avoidance system options for a
      broad spectrum of National Airspace System users.
[G.2] Detect potential midair collisions with other aircraft in all meteorological
      conditions.
R1.   Provide collision avoidance protection for any two aircraft closing horizontally
      at any rate up to 1,200 knots and vertically up to 10,000 feet per minute.
      Assumption: This requirement is derived from the assumption that commercial
      aircraft can operate up to 600 knots and 5,000 fpm during vertical climb or
      controlled descent ...
O1.   After the threat is resolved, the pilot shall return promptly and smoothly to
      his/her previously assigned flight path.
C1.   The system must use the transponders routinely carried by aircraft for ground
      ATC purposes.
SC3.  The system must not interfere with the ground ATC system or other aircraft
      transmissions to the ground ATC system.
  SC3.1.  The system design must limit interference with ground-based secondary
          surveillance radar, distance-measuring equipment channels, ...
    SC3.1.1. The design of the Mode S waveforms used by TCAS must provide
             compatibility with Modes A and C ...
E1.   Among the aircraft environmental alerts, the hierarchy shall be: Windshear has
      first priority, then the Ground Proximity Warning System (GPWS), then TCAS.
EA2.  All aircraft carry transponders.
EA5.  Threat aircraft will not make an abrupt maneuver that thwarts the TCAS escape
      maneuver.
L2.   TCAS provides no protection against aircraft with nonoperational transponders.
L5.   TCAS will not issue an advisory if it is turned on or enabled to issue
      resolution advisories in the middle of a conflict (→ FTA-405)
```

Level 2 (TSE 4.2.2; ESW pp. 339-341):

```
PR1.   Each TCAS-equipped aircraft is surrounded by a protected volume of airspace.
       The boundaries of this volume are shaped by the tau and DMOD criteria.
  PR1.1. TAU: In collision avoidance, time-to-go to the closest point of approach
         (CPA) is more important than distance-to-go to the CPA. ... Tau equals
         3,600 times the slant range in nmi, divided by the closing speed in knots.
PR2.   ALIM is the desired or "adequate" amount of separation between aircraft that
       TCAS is designed to meet. This amount varies from 400 to 700 feet ...
       (see PR22.3) ... (↑ SC4.5)
PR3.   Trade-offs must be made between necessary protection (G1) and unnecessary
       advisories (SC5). This is accomplished by controlling the sensitivity level ...
PR35.  Don't-Care-Test. When TCAS is displaying an RA against one threat and then
       attempts to choose a sense against a second threat ... One advantage is
       display continuity (↑ SC6). ...
PR36.2 A bias against altitude crossing RAs is also used in situations involving
       intruder level-offs at least 600 feet above or below the TCAS aircraft ...
       (↓ Alt_Separation_Test)
       Assumption: In most cases, the intruder will begin a level-off maneuver when
       it is more than 600 feet away ...
PR39.  Because of the limited number of inputs to TCAS for aircraft performance
       inhibits, in some instances where inhibiting RAs would be appropriate it is
       not possible to do so (↑ L3). ... (↑ SC9.1) ... (↓ [Pilot procedures on
       Level 3 and Aircraft Flight Manual on Level 4]).
```

Level 3 (TSE Figs. 4-7; ESW Fig. 10.12): a system interface topology diagram (own aircraft, pilot, displays and aural alerts, mode selector, TCAS, pressure altimeter, radio altimeter, A/C discretes, antennas, transmitter, Mode S transponder, air data computer, intruders, ground station); a SpecTRM-RL state-machine model of an environment component (radio altimeter with states operating-correctly, detected-failure, undetected-failure); and AND/OR tables for the CAS logic, for example the transition of INTRUDER.STATUS to Other-Traffic:

```
= Other-Traffic                                     OR
  Alt-Reporting in-state Lost        | T | T | T | . |
  Bearing-Valid                      | F | . | T | . |
  Range-Valid                        | . | F | T | . |
  Proximate-Traffic-Condition        | . | . | F | . |
  Potential-Threat-Condition         | . | . | F | . |
  Other-Aircraft in-state On-Ground  | . | . | . | T |
Description: A threat is reclassified as other traffic if its altitude reporting
  has been lost (↑2.13) and either the bearing or range inputs are invalid; ...
  or the aircraft is on the ground (↑2.12).
Mapping to Level 2: ↑2.23, ↑2.29
Mapping to Level 4: ↓4.7.1, Traffic-Advisory
```

Level 4: the MITRE pseudocode for the Don't-Care-Test (TSE Fig. 8), HCI design, the flight manual, physical requirements on transmitter and receiver, hardware design specs, verification requirements. Level 5: software, hardware assembly instructions, training plan, maintenance requirements.

## 2. The horizontal dimension: the four columns

TSE section 4.1: "Along these horizontal dimensions, intent specifications are broken up into four parts."

1. Environment: "information about characteristics of the environment that affects the ability to achieve the system goals and design constraints. For example, in TCAS, the designers need information about the operation of the ground-based ATC system in order to fulfill the system-level constraint of not interfering with it. ... the design of the surveillance logic in TCAS depends on the characteristics of the transponders carried on the aircraft with which the surveillance logic interacts."
2. Operator: "information about human operators or users. Too often human factors design and software design is done independently." The goal is "to integrate the information needed to design human-centered automation into the system requirements specification."
3. System: "the system itself and its decomposition into subsystems or components."
4. V&V: "each level also includes information about the verification and validation activities and results appropriate for that specification level."

ESW Fig. 10.2 ("An example of the information in an intent specification") fills in every cell:

| Level | Environment | Operator | System and components | V&V |
|---|---|---|---|---|
| 0 Prog. Mgmt. | Project management plans, status information, safety plan, etc. (spans all columns) | | | |
| 1 System Purpose | Assumptions, Constraints | Responsibilities, Requirements, I/F requirements | System goals, high-level requirements, design constraints, limitations | Preliminary Hazard Analysis, Reviews |
| 2 System Principles | External interfaces | Task analyses, Task allocation, Controls, displays | Logic principles, control laws, functional decomposition and allocation | Validation plan and results, System Hazard Analysis |
| 3 Blackbox Models | Environment models | Operator Task models, HCI models | Blackbox functional models, Interface specifications | Analysis plans and results, Subsystem Hazard Analysis |
| 4 Design Rep. | | HCI design | Software and hardware design specs | Test plans and results |
| 5 Physical Rep. | | GUI design, physical controls design | Software code, hardware assembly instructions | Test plans and results |
| 6 Operations | Audit procedures | Operator manuals, Maintenance, Training materials | Error reports, change requests, etc. | Performance monitoring and audits |

In the 1999 TCAS document the columns appear as sections rather than as a physical grid: 1.3 Environment, 1.4 Operator, 2.5 Pilot-TCAS Interface, 2.6 Testing and Validation, 3.1 Environment, 3.2 Flight Crew Requirements, 3.5 Testing Requirements, 4.1 HCI Design, 4.6 Verification Requirements, 5.3 Training. ESW confirms the mapping is logical, not physical: "the particular organization used for the TCAS specification is simply one possible physical realization of the general logical organization inherent in intent specifications" (TSE conclusions).

## 3. The means-ends principle and the reference notation

### The principle

TSE 3.3.3: "In a means-end abstraction, each level represents a different model of the same system. At any point in the hierarchy, the information at one level acts as the goals (the ends) with respect to the model at the next lower level (the means). Thus, in a means-ends abstraction, the current level specifies what, the level below how, and the level above why." And: "Mappings between levels are many-to-many: Components of the lower levels can serve several purposes, while purposes at a higher level may be realized using several components of the lower-level model. These goal-oriented links between levels can be followed in either direction, reflecting either the means by which a function or goal can be accomplished (a link to the level below) or the goals or functions an object can affect (a link to the level above)."

The JPL 2007 report puts it operationally: "An up arrow denotes that the current specification item is involved in the implementation of the intent of a specification item at a higher level in the means-ends hierarchy denoted by the tag after the arrow. A down arrow points to a specification item at a lower level ... that is involved in the implementation of the intent of the current specification item. Left and right arrows denote relationships between specification items at the same level ... A left arrow points to a specification item at the same level that appears earlier in the specification than the current specification item. Conversely, a right arrow points to another specification item at the same level that appears later."

### ID scheme in the actual 1999 TCAS document

From the preface (pp. ii-iii): "In this document, we try to use industry standard terminology where 'shall' denotes a requirement, 'should' denotes an option, 'must' represents a constraint, and 'will' denotes an assumption about the environment. ... Mappings are indicated by pointers, but an electronic version of this type of specification could use sophisticated hyper-text links including multiple windows to denote these relationships. The first number or letters of a link tells you where it is located:

```
Number 1-5: Requirement on Levels 1 to 5
G:     Goal (Level 1)
EA:    Environmental Assumption (Level 1)
EC:    Environment Constraint (Level 1)
OP:    Operator behavioral requirement, assumption, or constraint (Level 1)
L:     Limitation (Level 1)
C:     Non-safety-related design constraint (Level 1)
SC:    Safety-related design constraint (Level 1)
FTA-x: Line x of the Fault Tree Analysis
```

Items are headed by a bracketed tag on its own line and links sit in parentheses at the end of the sentence. Verbatim from pp. 29 and 33:

```
[C.4]
TCAS must comply with all applicable FAA and FCC policies, rules, and
philosophies (↓2.30, 2.79).

[SC4.5]
TCAS must allow for increased altimetry error as altitude increases (↓2.1, 2.32).

[SC4.8]
If there are more traffic advisories to generate than can be accomodated on
the screen, a priority must be used based on severity (↓2.22, →FTA-375, FTA-735).

[SC5]
The system must operate with an acceptably low level of unwanted or nuisance
alarms. ... (↓2.2.3, 2.5.2, 2.32, 2.43, 2.44).
    [SC5.1]
    The system must control synchronous garbling, nonsynchronous garbling, and
    ground-reflected (multipath) signals (↓2.10, 2.11, 2.12, Page 61).
        [SC5.1.1]
        The probability that a surveillance track based on FRUIT replies will be
        started and maintained must be extremely remote (↓2.11, 2.12).
```

Note the mixed conventions even inside one document: "[C.4]" with a dot but "[SC4.5]" without, and a link that is a bare page number ("Page 61"). Level 2 items are referred to by their section number (2.30, 2.2.3), not by a PR prefix, in the 1999 document; the TSE paper's PR1/PR36.2 labels and ESW's 2.2/2.36.2 labels are two renderings of the same items.

### Notation in the 2000 paper and in ESW

The TSE paper uses arrows the same way: "L5. ... (→ FTA-405)" with footnote "The pointer to FTA-405 denotes the box labeled 405 in the Level-1 fault tree analysis"; "PR36.2 ... (↓ Alt_Separation_Test m-351)"; "PR39 ... (↑ L3) ... (↑ SC9.1) ... (↓ [Pilot procedures on Level 3 and Aircraft Flight Manual on Level 4])"; "PR38 ... (↑ SC7.1, FTA-1150) ... (↑ SC8.1)". ESW examples (pp. 332-341):

```
C.4: TCAS must comply with all applicable FAA and FCC policies, rules, and
     philosophies (↓2.30, 2.79).
SC.3: TCAS must generate advisories that require as little deviation as possible
     from ATC clearances (→ H6, HA-550, ↓2.30).
SC.6: TCAS must not disrupt the pilot and ATC operations during critical phases
     of flight nor disrupt aircraft operation (→ H3, ↓2.2.3, 2.19, 2.24.2).
   SC.6.1: The pilot of a TCAS-equipped aircraft must have the option to switch to
     the Traffic-Advisory-Only mode ... (↓ 2.2.3).
     Assumption: This feature will be used during final approach to parallel
     runways ... (↓ 6.17).
SC.7.1: Crossing Maneuvers must be avoided if possible (↓ 2.36, ↓ 2.38, ↓ 2.48,
     ↓ 2.49.2).
OP.4: After the threat is resolved, the pilot shall return promptly and smoothly to
     his/her previously assigned flight path (→ HA-560, ↓3.3).
1.18: TCAS shall provide collision avoidance protection for any two aircraft
     closing horizontally at any rate up to 1200 knots ...
     Assumption: ...
2.2: Each TCAS-equipped aircraft is surrounded by a protected volume of airspace.
     The boundaries of this volume are shaped by the tau and DMOD criteria (↑1.20.3).
   2.2.2: DMOD: ... (→ 2.2.4).
2.51: Sense Reversals: (↓ Reversal-Provides-More-Separation) In most encounter
     situations, the resolution advisory will be maintained ... (↑SC-7.2). ...
     (↑HA-130). ... (↑HA-395).
2.36.2: A bias against altitude crossing RAs ... (↑SC.7.1). ... (↓ Alt_Separation_Test).
2.39: ... (↑L6). ... (↑SC9.1). ... (↓ [Pointers to pilot procedures on level 3 and
     Aircraft Flight Manual on level 6).
L1: TCAS provides no protection against aircraft without transponders or with
     nonoperational transponders (→EA3, HA-430).
L6: ... (→H3, ↓2.38, 2.39).
```

So the target of a link can be a numbered item (2.30), a tagged item (SC-7.2, HA-395, EA3, H6), a named Level 3 model element (Alt_Separation_Test, Reversal-Provides-More-Separation), or a fault tree line (FTA-405). Level 3 SpecTRM-RL tables carry a link block "Mapping to Level 2: ↑2.23, ↑2.29 / Mapping to Level 4: ↓4.7.1, Traffic-Advisory" plus inline up-links in the Description text. Variables in tables have subscripts giving their kind and page: "Auto-SL s-241" (state), "Lowest-Ground f-400" (function), "Mode-Selector v-218" (input variable), "Bearing-Valid m-478" (macro), "t" for table.

### Later notations by her students

The JPL 2007 report writes links as parenthesised groups by direction, with element-name prefixes: "A&AC-G1. ... (←S/C-R1), (↓2.2, S/C-2.3, C&DH-2.1.6, SV-1, SV-2), (→A&AC-R1, A&AC-R2 ...)"; "A&AC-SC1 ... (←H1, H2, H5, H6, H7), (↓A&AC-2.2.1.4, ...), (→A&AC-ICA10, ...)"; hazards are structured records: "H1. Inability of Mission to collect data. (↓SV-85) / System Element: ... / Causal Factors: ... (←C&DH-CF1.1 ...) / Level and Effect: ... (↑ACC4) / Safety Constraints: ... (→SC1)". Each item may carry a "Rationale:" line. The Weiss papers use square-bracket hyperlinks and prefix cross-document targets with the document name: "[FR.1] The RWA shall receive commands from the ADCS once per second ... [DP.1]" and "[EC.1] There is only one Ground Station ... [L.1] [DP.1.3] [TeleSub EC.2] [Transmitter EA.3] [Antenna EA.3] [Receiver EA.3] [Ground L.1]".

### Bidirectional? Across columns?

Bidirectional in intent and mostly in practice. TSE: "Safety-related constraints should have two-way links to the system hazard log." ESW: "The hazard analysis portion labeled HA-395 would have a complementary pointer to section 2.51." ESW p. 341: "two-way tracing should exist between the component requirements and the system design principles and requirements." The 1999 document is not perfectly symmetric because Level 4 is imported pseudocode with only upward comments planned ("The software itself (Level 5) would contain comments about implementation decisions and also a pointer up to the Level 4 design documentation"). Links cross columns freely: operator requirements OP.4/OP.9 link to hazard analysis (system V&V column) and to Level 2 and 3 design; environment assumptions EA3 are linked from limitations L1; Level 2 principles link to pilot procedures (operator column, Level 3) and the flight manual (Level 6).

## 4. The third dimension: refinement vs decomposition vs means-ends

TSE Fig. 2 draws a cube with three axes: Intent (vertical), Decomposition (horizontal across the four columns and across components within the system column), and Refinement (depth). Section 4.1: "Computer science commonly uses two types of part-whole abstractions. Parallel decomposition (or its opposite, aggregation) separates units into (perhaps interacting) components of the same type. In Statecharts, for example, these components are called orthogonal components ... The second type of part-whole abstraction, refinement, takes a function and breaks it down into more detailed steps. An example is the combining of a set of states into a superstate in Statecharts. ... In programming, refinement abstractions are represented by procedures or subprograms. Note that neither of these types of abstraction is an emergent-property or means-ends abstraction; the whole is simply broken up into a more detailed description. Additional information, such as intent, is not provided at the higher level."

ESW restates it as "three dimensions: intent abstraction, part-whole abstraction, and refinement" and adds the key rule: "Refinement and decomposition occurs within each level of the specification, rather than between levels. Each level provides information not just about what and how, but why." The JPL report: "Levels do not represent refinement, as in other commonly used hierarchical specification frameworks. Instead, each level of an intent specification represents a completely different model of the same system ... The model at each level is described in terms of a different set of attributes or language."

In the document, refinement is shown by dotted numbering inside one level (SC3 → SC3.1 → SC3.1.1; 2.2 → 2.2.1; "Note that refinement occurs at the same level of the intent specification"). In SpecTRM-RL, breaking a large AND/OR table into macros is "a form of refinement abstraction". Decomposition is the split of the system column into subsystems (TCAS → surveillance, CAS, performance monitoring) and the topology diagram at Level 3. The test for a means-ends step is that the language changes: Level 1 is English goals and constraints, Level 2 is physics and control principles (tau, DMOD, ALIM), Level 3 is a state machine over inputs and outputs, Level 4 is pseudocode, Level 5 is code.

## 5. Domain-specific versus generic

Leveson's own scope statement (TSE section 4): "The exact number and content of the means-ends hierarchy levels may differ from domain to domain. Here, a structure is presented for process systems with shared software and human control." And (conclusions): "intent specifications are a logical abstraction that can be realized in many different physical ways."

Generic parts: the means-ends stack with different language per level; refinement and decomposition confined within a level; the four-column split (environment, operator, system, V&V); tagged items with bidirectional links; separate Assumption and Rationale entries under any item; the distinction between goals ("purpose"), requirements ("testable and achievable" shall-statements refined from goals), design constraints ("restrictions on how the system can achieve its purpose"), and limitations ("accepted risks", placed at Level 1 "because they properly belong in the customer view"); evaluation criteria and priorities for resolving conflicts; the rule that Level 4 design decisions unrelated to requirements ("the use of a particular graphics package because the programmers are familiar with it") are allowed to be unlinked and "Knowing that these decisions are not linked to higher level purpose is important during software maintenance."

Safety-critical / control-system parts: accidents at Level 0 (JPL); hazards (H1...), the hazard log and hazard analysis at Level 1 (fault tree with FTA-x lines in 1999; STPA with HA-x in ESW); the SC versus C split; the operator column's task analysis, task allocation, controls and displays, HCI models, mode confusion analysis; environment component models "including, perhaps, failure behavior, upon which the correctness of the system design is predicated"; the requirement that Level 3 be an executable process-control state-machine language (RSML, then SpecTRM-RL) whose syntax encodes the Safeware completeness criteria, with AND/OR tables reviewable by domain experts; the Level 6 operations column for auditing assumptions ("The operational system should be monitored to ensure ... that the models and assumptions used during initial decision making and design were correct"); and the emphasis on control flow over data flow ("specifications for embedded controllers may emphasize control flow over data flow ... while data transformation or information management systems might place more emphasis on the specification of data flow").

## 6. Composition, nesting, and the enclosing system

### Leveson's answer: the parent system is the environment

TSE 4.2.3: "Remember that the boundaries of a system are purely an abstraction and can be set anywhere convenient for the purposes of the specifier. In this case, any component that was already on the aircraft or in the airspace control system and was not newly designed or built as part of the TCAS effort was included as environment." The TCAS document has Level 1 section 1.3 (Environmental Assumptions EA, Environmental Constraints EC), Level 3 section 3.1 (environment component models), and appendix E "Performance Requirements on Equipment that Interacts with TCAS".

ESW makes the enclosing-system role explicit (pp. 328-333): E1-E3 are "requirements for the integration of the new subsystem safely into the larger system"; SC.2 and its refinements "stem from a high-level environmental constraint derived from safety considerations in the encompassing system into which TCAS will be integrated"; and "these assumptions must be enforced in the overall safety control structure. With respect to assumption EA4, for example, identification numbers are usually provided by the aviation authorities in each country ... The assumption that aircraft have operating transponders (EA3) may be enforced by the airspace rules in a particular country". ESW also distinguishes "assumptions that originate in the existing environment into which the new system will be integrated" from "assumptions that the emerging system design imposes on the surrounding environment", which "will become clear only after detailed decisions are made". The enclosing control structure itself (ICAO, FAA, local ATC ops management, airline ops management, controller, pilot, TCAS, aircraft) is drawn in ESW Fig. 10.10 as part of the STPA analysis, not as a parent intent spec. The 1999 TCAS document does not reference any enclosing aircraft or airspace intent specification.

### Explicit nesting by her students

Weiss, Ong, Leveson (incose.pdf) define "SpecTRM-GCs (SpecTRM Generic Components)", each a complete intent specification of one component: "each component is fully encapsulated, it has well-defined interfaces, it is generic, and it contains component-level fault protection." A component's Level 1 carries its own assumptions about its parent: "[FR.1] The RWA shall receive commands from the ADCS once per second ... [DP.1] Assumption: The ADCS commands will be in the form of torque values to be applied on each of the spacecraft's three axes." and "Note the need to provide relevant operational environment assumptions that the RWA design makes about any potential spacecraft that uses this RWA specification." Items that a reusing project must fill in are shown in bold underline.

Weiss et al. 2006 (AIAA-Weiss.pdf, section D) build a three-tier tree of documents: "At the highest level, the Spacecraft Mission and CDHC document describe the project as a whole ... At the Subsystem-Level, the Telecommunication Subsystem (TeleSub) was modeled. Finally, at the component-level, Levels 1 and 2 of Transmitters, a Receiver and an Antenna were defined. These component-level specifications interact with their parent Subsystem, the TeleSub. The TeleSub interacts with the CDHC." Links work "within the document as well as between documents, allowing users to link high-level design decisions to subsystem and component designs and vice versa", and a child's environment assumptions "are justified by tracing them to the section in the other intent specifications that validates them." The cross-document link syntax prefixes the target document name: "[EC.1] There is only one Ground Station for spacecraft communications ... [L.1] [DP.1.3] [TeleSub EC.2] [Transmitter EA.3] [Antenna EA.3] [Receiver EA.3] [Ground L.1]". Level 2 of the mission spec (orbit altitude and inclination) flows down to Level 2 of the transmitter spec (data rate, frequency, power).

The JPL 2007 report chooses the other option: one document with element sections nested inside each level. "Step 9: Define System Element Specifications ... Define goals, assumptions, requirements, design constraints and safety constraints for each subsystem or functional element at level 1", giving headings like "Level 1.1.3: Spacecraft Attitude and Articulation Control (A&AC) Goals, Requirements, and Constraints" and element-prefixed tags (A&AC-G1, A&AC-SC1, C&DH-SC2, S/C-R1, HA&T-2.1) that link across elements and levels.

## 7. Critiques, extensions, follow-on work, adoption

Extensions from Leveson's group:
- Navarro, Lundqvist, Leveson, "An intent-specifications model for a robotic software control system" (IEEE, 2001; NASA shuttle tile-servicing robot). https://ieeexplore.ieee.org/document/964239/
- Navarro, Leveson, Lundqvist, "Reducing the Effects of Requirements Changes through System Design" (coupling.pdf) and "Semantic decoupling: reducing the impact of requirement changes", Requirements Engineering 15(4), 2010, pp. 419-437, DOI 10.1007/s00766-010-0109-5. Uses traceability matrices across intent-spec levels to measure sensitivity to requirement changes. https://dspace.mit.edu/entities/publication/093a51c9-5336-4a4d-ba40-974b0f9abf88
- Dulac, Viguier, Leveson, Storey, "On the Use of Visualization in Formal Requirements Specification", RE 2002. http://sunnyday.mit.edu/papers/RE02_visualization.pdf ; MIT SM thesis 2004, "System design visualizations for synthesizing intent specifications". https://dspace.mit.edu/entities/publication/332fbf72-d57b-437a-8f53-851834efddf6
- Weiss, Ong, Leveson: reusable component intent specs (incose.pdf, components.pdf); Weiss et al. 2006 JACIC; Weiss SM thesis "Building a Reusable Spacecraft Architecture using Component-Based System Engineering" (MIT 2003).
- Stringfellow, "Safety-Driven System Engineering Process" (MIT thesis) and the JPL Part I/II reports integrating STAMP, STPA, intent specs, and JPL State Analysis. https://dspace.mit.edu/server/api/core/bitstreams/ae9cc78d-d2d4-4ba7-9c41-0a5fba1ccd0d/content
- ESW itself: fault trees replaced by STPA, Level 0 and Level 6 added, safety-driven design.
- Commercial: Safeware Engineering Corporation's SpecTRM tool, funded by NASA SBIRs (https://spinoff.nasa.gov/spinoff2003/ct_10.html, https://www.sbir.gov/portfolio/296184).

Outside MIT:
- FAA AR-08-34 (2009) reviews SpecTRM/intent specs alongside SCR, CoRE, RSML, and UML/SysML. It is favourable: a SpecTRM-RL model "is embedded within a larger intent specification that provides a seamless flow of rationale and reasoning from the highest level goals of the system, down through the SpecTRM-RL model all the way down to the implementation and operator training materials", and "the process for developing an Intent Specification elevates the development of the requirements for the HMI to a separate process that proceeds in parallel with the development of the system itself and the safety process." It recommends intent specs for conveying rationale to IMA application teams.
- NASA CertWare (Eclipse, Xtext) ships "an intent specification DSL model for design and hazard support" (*.intent files) plus an STPA DSL; last documented around 2016. https://github.com/nasa/CertWare
- KTH automotive: Mohan 2018 licentiate thesis cites Leveson for "documentation of not just the requirements of a system but also the design decisions, their assumptions and rationale" and adapts a "safety intent specification"; Westman, Nyberg, Törngren (SAFECOMP 2015, "Structuring Safety Requirements in ISO 26262 Using Contract Theory") cite intent specs for documenting assumptions. https://arxiv.org/abs/2001.02496
- Goal-oriented RE surveys (van Lamsweerde, Lapouchnian) list intent specifications as one rationale-capturing approach next to KAOS, i*, gIBIS/QOC, but without detailed comparison.

Critiques: no substantial published critique aimed at the format itself was found. The weaknesses on record are mostly Leveson's own admissions: evaluation criteria and priorities were left out of the TCAS spec because she "was unable to find out how these decisions were made during the TCAS design process"; a safety constraint such as "extremely rare" is "clearly vague and untestable"; new kinds of Level 4 content have "practicality [that] needs to be determined"; and the whole approach rests on "a basic hypothesis" from cognitive-psychology literature rather than on an experiment with intent specs. Practical adoption looks thin: Safeware Engineering's trademark was cancelled in 2016 and no current vendor was found; the Level 3 language requires a specific executable tool; Mohan notes "the overhead of introducing heavy processes into an organization"; and the FAA survey found only one industry comment about HMI requirements despite Leveson's emphasis. Recent papers using the phrase "intent specification" (DARPA IDAS; "Intent-Driven Programming in FAST", arXiv 1907.08695; "Intent-based System Design and Operation", arXiv 2502.05984; "Semantic Commit: Helping Users Update Intent Specifications for AI Memory at Scale", UIST 2025) define the term independently and do not cite Leveson.

## 8. Lightweight, plain-text, or Markdown adaptations

None found that derive from Leveson. The nearest things:
- Leveson's own statement (ESW p. 313): "most of the principles can be implemented without special tools beyond a text editor and hyperlinking facilities. The rest of this chapter assumes only these very limited facilities are available."
- The 1999 TCAS document is effectively plain text produced with LaTeX: bracketed tags on their own line, arrows and dotted numbers in trailing parentheses, Assumption/Rationale sub-paragraphs, and a preface that defines the tag prefixes. That maps directly onto Markdown headings, anchors, and links.
- The Weiss "[Doc Tag]" convention is the only worked example of cross-file links between parent and child intent specs.
- CertWare's Xtext DSL is the only machine-readable grammar, and it is Eclipse-bound rather than plain text.
- Nothing on GitHub or in the literature was found that presents a Markdown template for Leveson-style intent specs; the "intent-driven" and "spec-driven development" templates that turn up in searches are unrelated.
