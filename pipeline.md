# **Synthetic Population Pipeline: IPF and Post-Processing**

This document outlines the pipeline for generating a synthetic population at the buurt (neighborhood) level using CBS datasets. The methodology uses a Star Schema approach around the Leeftijd (Age) variable to avoid infinite oscillation in the Iterative Proportional Fitting (IPF) algorithm.

## **Variable Mapping and Optimization Phase**

The table below maps the variables from the variables.md catalog to their respective processing phase.

| Variable | CBS Table | IPF Phase | Rationale |
| :---- | :---- | :---- | :---- |
| **Buurtcode** | 86165NED | **IPF Constraints** | The spatial anchor. |
| **Bevolkingsomvang** | 86165NED | **IPF Constraints** | Total weight constraint per neighborhood. |
| **Leeftijdsverdeling** | 86165NED | **Seed & IPF** | The central spine. Local margins limit the national seed. |
| **Migratieachtergrond** | 86165NED & 83931NED | **Seed & IPF** | Jointly seeded with Age/Income; constrained locally. |
| **Inkomen** | 86165NED & 83931NED | **Seed & IPF** | Jointly seeded with Age/Mig; constrained locally. |
| **Huishoudsamenstelling** | 86165NED & 37312 | **Seed & IPF** | Jointly seeded with Age; constrained locally. |
| **Opleidingsniveau** | 85321NED | **Seed** | Seeded with Age/Employment to preserve structural links. No strict local marginals available in 86165NED, so it emerges from the IPF projection. |
| **Arbeidsdeelname** | 85321NED | **Seed** | Seeded with Age/Education. Emerges from IPF projection. |
| **Schoolgaande kinderen** | 86165NED (derived) | **Post-Processing** | Derived via integer age imputation after IPF completes. |
| **Woon-werkafstand** | 84709NED | **Post-Processing** | Behavioral outcome. Assigned via Monte Carlo simulation conditioned on Employment and Age. |
| **Landgebruik (Groen/Water)** | 70262NED | **Post-Processing** | Spatial metadata. Deterministic relational join via Buurtcode. |
| **Autobezit (Could-have)** | 86165NED | **Post-Processing** | Assigned probabilistically based on Household composition. |
| **Nabijheid Zorg (Could-have)** | 85870NED | **Post-Processing** | Spatial metadata. Deterministic relational join via Buurtcode. |

## **Phase 1: Seed Preparation (National / Municipal Level)**

The objective is to create a single N-dimensional seed matrix representing the "global prior" of demographic correlations, avoiding conflicting overlapping margins.

1. **Extract Joint Tables:** Pull 83931NED (Age × Mig × Inc), 37312 (Age × HH), and 85321NED (Age × Edu × Emp).  
2. **Taxonomy Alignment:** Aggregate the granular age bins in the joint tables to match the coarse bins required by the local constraints (0–14, 15–24, 25–44, 45–64, 65+).  
3. **Spine Harmonization:** Extract the 1D national Age distribution. Force-scale the marginalized Age distributions of 83931NED, 37312, and 85321NED to perfectly match this single national Age array.  
4. **Seed Matrix Calculation:** Generate a Cartesian product DataFrame of all variable categories. Calculate the base weight (total) for each row by applying the Naive Bayes assumption of conditional independence given Age:  
   P(Row) \= P(Age) \* P(Mig, Inc | Age) \* P(HH | Age) \* P(Edu, Emp | Age)  
5. **Structural Zeros:** Hardcode impossible combinations to 0.0 (e.g., Age 0-14 and Master's degree) to speed up convergence and enforce logic.

## **Phase 2: Local IPF Execution**

The algorithm is executed iteratively, isolating one buurt at a time to prevent spatial contradiction.

1. **Target Extraction:** For a specific buurt, extract the 1D marginal totals for Age, Migration Background, Income, and Household Size from 86165NED.  
2. **Matrix Initialization:** Load the N-dimensional Seed Matrix generated in Phase 1\.  
3. **IPF Run:** Execute ipfn.  
   * original \= Seed Matrix  
   * aggregates \= The four 1D marginals for the specific buurt.  
   * The algorithm scales the national conditional probabilities to respect the local constraints while minimizing Kullback-Leibler divergence.  
4. **Iteration:** Repeat for all targeted neighborhoods. Append the resulting fractional dataframes.

## **Phase 3: Microdata Instantiation & Post-Processing**

The output of Phase 2 is an aggregate table of fitted weights. It must be converted into a micro-level dataset of distinct actors.

1. **Instantiation:** Apply stochastic rounding to the fitted weights. Expand the rows so that a weight of 50 becomes 50 distinct rows. Assign a unique Actor\_ID.  
2. **Integer Age Imputation:** For actors in the "0-14" and "15-24" brackets, draw an integer age from the national 1-year age distribution (03759NED).  
3. **School-Going Flag:** Evaluate the integer age. If the actor is between 4 and 17, flag Schoolgaand \= True.  
4. **Spatial Joins (Meta/Context):** Perform a left join on the microdata using Buurtcode against tables 70262NED and 85870NED to append environmental percentages (Groen/Water) and distances to hospitals.  
5. **Behavioral Assignment (Mobility):** \* Isolate actors where Arbeidsdeelname \== True.  
   * Query the ODiN dataset (84709NED) to find the probability distribution of commute distance for their specific Age and Income bracket.  
   * Use weighted random selection (np.random.choice) to assign a specific woon\_werkafstand.