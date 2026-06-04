# **Synthetic Population Pipeline: IPF and Post-Processing**

This document outlines the pipeline for generating a synthetic population at the buurt (neighborhood) level. The methodology uses a Star Schema approach around the Leeftijd (Age) variable to avoid infinite oscillation in the Iterative Proportional Fitting (IPF) algorithm.

## **Variable Mapping: Must-Haves**

These variables form the core of the synthetic demographic and socio-economic projection.

| Variable | Source Dataset | Distribution Level | Joint With | Pipeline Phase |
| :---- | :---- | :---- | :---- | :---- |
| **Buurtcode** | 86165NED | Marginal (Buurt) | None | **Constraints** |
| **Bevolkingsomvang** | 86165NED | Marginal (Buurt) | None | **Constraints** |
| **Leeftijdsverdeling** | 86165NED 83931NED 37620 85321NED | Marginal (Buurt) Joint (National) Joint (National) Joint (National) | None Mig, Inc HH-type Edu, Emp | **Constraints Seed Seed Seed** |
| **Migratieachtergrond** | 86165NED 83931NED | Marginal (Buurt) Joint (National) | None Leeftijd, Inkomen | **IPF Seed** |
| **Inkomen (Persoon)** | 86165NED 83931NED | Marginal (Buurt) Joint (National) | None Leeftijd, Migratie | **IPF Seed** |
| **Huishoudsamenstelling** | 86165NED 37620 | Marginal (Buurt) Joint (National) | None Leeftijd, Geslacht | **IPF Seed** |
| **Opleidingsniveau** | 85321NED | Joint (National) | Leeftijd, Arbeidsdeelname | **Seed** |
| **Arbeidsdeelname** | 85321NED | Joint (National) | Leeftijd, Opleiding | **Seed** |
| **Schoolgaande kinderen** | 03759NED (proxy) | Marginal (National) | None | **Post-Processing** |
| **Woon-werkafstand** | 84709NED (ODiN) | Joint (Provincial) | Leeftijd, Arbeidsdeelname | **Post-Processing** |
| **Landgebruik (Groen/Water)** | 70262NED | Marginal (Buurt) | None | **Post-Processing** |

## **Variable Mapping: Should-Haves**

These variables provide physical, infrastructural, and household-level context. They are largely deterministic or spatial attributes applied after the demographic core is generated.

| Variable | Source Dataset | Distribution Level | Joint With | Pipeline Phase |
| :---- | :---- | :---- | :---- | :---- |
| **Stedelijkheidsgraad** | 86165NED | Marginal (Buurt) | None | **Post-Processing** |
| **Woningtype (Huur/Koop, Eengezins)** | 86165NED | Marginal (Buurt) | None | **Post-Processing** |
| **Bezettingsgraad / Huishoudgrootte** | 86165NED | Marginal (Buurt) | None | **Post-Processing** |
| **Besteedbaar inkomen per huishouden** | 86165NED 83932NED | Marginal (Buurt) Joint (National) | None HH-samenstelling | **Post-Processing** |
| **Autobezit** | 86165NED | Marginal (Buurt) | None | **Post-Processing** |
| **RWZI: ID, Naam, Locatie, Capaciteit** | RWS / RIVM Open Data | Meta (National) | None | **Post-Processing** |
| **RWZI: Catchment-opp. / aansluitingen** | RWS / Waterschappen | Meta (Catchment) | None | **Post-Processing** |
| **Nabijheid (lucht)haven** | GIS / OpenStreetMap | Meta (Local) | None | **Post-Processing** |

## **Phase 1: Seed Preparation (National Level)**

The objective is to create a single N-dimensional seed matrix representing the "global prior" of demographic correlations, avoiding conflicting overlapping margins.

1. **Extract Joint Tables:** Pull 83931NED (Age × Mig × Inc), 37620 (Age × HH), and 85321NED (Age × Edu × Emp).  
2. **Taxonomy Alignment:** Aggregate the granular age bins in the joint tables to match the coarse bins required by the local constraints (0–14, 15–24, 25–44, 45–64, 65+).  
3. **Spine Harmonization:** Extract the 1D national Age distribution. Force-scale the marginalized Age distributions of 83931NED, 37620, and 85321NED to perfectly match this single national Age array.  
4. **Seed Matrix Calculation:** Generate a Cartesian product DataFrame of all variable categories. Calculate the base weight (total) for each row by applying the Naive Bayes assumption of conditional independence given Age:  
   P(Row) \= P(Age) \* P(Mig, Inc | Age) \* P(HH | Age) \* P(Edu, Emp | Age)  
5. **Structural Zeros:** Hardcode impossible combinations to 0.0 (e.g., Age 0-14 and Master's degree) to speed up convergence.

## **Phase 2: Local IPF Execution**

The algorithm is executed iteratively, isolating one buurt at a time to prevent spatial contradiction.

1. **Target Extraction:** For a specific buurt, extract the 1D marginal totals for Age, Migration Background, Individual Income, and Household Size from 86165NED.  
2. **Matrix Initialization:** Load the N-dimensional Seed Matrix generated in Phase 1\.  
3. **IPF Run:** Execute ipfn.  
   * original \= Seed Matrix  
   * aggregates \= The four 1D marginals for the specific buurt.  
4. **Iteration:** Repeat for all targeted neighborhoods. Append the resulting fractional dataframes.

## **Phase 3: Microdata Instantiation & Post-Processing**

The aggregate table of fitted weights is converted into discrete actors and augmented with contextual data.

1. **Instantiation:** Apply stochastic rounding to the fitted weights. Expand the rows so that a weight of 50 becomes 50 distinct rows. Assign a unique Actor\_ID.  
2. **Integer Age & School Flag:** Draw an integer age from 03759NED for actors in the "0-14" and "15-24" brackets. If the integer age is 4–17, set Schoolgaand \= True.  
3. **Behavioral Assignment (Mobility):** Isolate actors where Arbeidsdeelname \== True. Query ODiN (84709NED) for the probability distribution of commute distance for their Age/Income. Execute a weighted random selection.  
4. **Household Aggregation:** Group individuals by Buurtcode and Huishoudsamenstelling to form distinct households. Aggregate individual incomes to calculate the **Besteedbaar inkomen per huishouden**, calibrating against the neighborhood averages in 86165NED.  
5. **Dwelling Assignment:** Probabilistically assign **Woningtype** (rent/own, single/multi-family) and **Autobezit** to the grouped households based on the marginal distributions in 86165NED.  
6. **Spatial Meta-Joins (Buurt Level):** Perform a left join on Buurtcode to append **Stedelijkheidsgraad**, **Landgebruik** (70262NED), and GIS-calculated distances to infrastructure (**luchthaven/haven**).  
7. **Epidemiological Meta-Joins (Catchment Level):** Perform a spatial intersection mapping Buurtcode centroids to RWZI catchment areas. Append **RWZI ID, naam, capaciteit, en opp.** from the RWS/RIVM registers to the actors in those neighborhoods.