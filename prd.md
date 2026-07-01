                                                                                                                                                                                                    
 Product Requirements Document (PRD)                                                                                                                                                                
                                                                                                                                                                                                    
 Project Codename: Crisis-Cost Orchestrator                                                                                                                                                         
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 1. Executive Summary                                                                                                                                                                               
                                                                                                                                                                                                    
 Vision: A decentralized, real-time economic orchestrator that guarantees no patient faces medical bankruptcy for emergency/acute care—while ensuring healthcare systems remain financially         
 sustainable.                                                                                                                                                                                       
                                                                                                                                                                                                    
 Problem: Current healthcare cost structures expose patients to unaffordable bills for emergency care, leading to medical bankruptcies, reduced care-seeking behavior, and systemic inefficiencies. 
                                                                                                                                                                                                    
 Solution: An AI-driven, HIPAA-compliant platform that classifies care events as "Emergency" in real-time, triggers pre-negotiated subsidies, and caps out-of-pocket costs at 10% of annual income  
 for qualifying patients.                                                                                                                                                                           
                                                                                                                                                                                                    
 Unique Value Proposition:                                                                                                                                                                          
 Protects 90% of patients from catastrophic emergency costs while creating a sustainable, data-driven payment ecosystem for providers and insurers.                                                 
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 2. Background & Market Context                                                                                                                                                                     
                                                                                                                                                                                                    
 ### 2.1. Market Size & Pain Points                                                                                                                                                                 
                                                                                                                                                                                                    
 - US Healthcare Spend: $4.9T annually (2024)                                                                                                                                                       
 - Medical Bankruptcy Rate: 66% of all bankruptcies linked to medical issues (American Journal of Public Health)                                                                                    
 - Emergency Care Costs: Average ER visit = $2,200; uninsured patients often receive no cost warnings                                                                                               
 - Regulatory Pressure: No Surprises Act (2022), state-level price transparency laws                                                                                                                
                                                                                                                                                                                                    
 ### 2.2. Competitive Landscape                                                                                                                                                                     
                                                                                                                                                                                                    
 ┌──────────────────────────────────┬─────────────────────────────────┬───────────────────────────────────────────┐                                                                                 
 │ Entity                           │ Offering                        │ Gap                                       │                                                                                 
 ├──────────────────────────────────┼─────────────────────────────────┼───────────────────────────────────────────┤                                                                                 
 │ Traditional Insurers             │ Retrospective claims processing │ No real-time affordability protection     │                                                                                 
 ├──────────────────────────────────┼─────────────────────────────────┼───────────────────────────────────────────┤                                                                                 
 │ Healthcare.gov / State Exchanges │ Static plan comparison          │ No dynamic cost modeling                  │                                                                                 
 ├──────────────────────────────────┼─────────────────────────────────┼───────────────────────────────────────────┤                                                                                 
 │ GoodRx / Mark Cuban Health       │ Rx pricing transparency         │ Limited to pharmacy, not acute care       │                                                                                 
 ├──────────────────────────────────┼─────────────────────────────────┼───────────────────────────────────────────┤                                                                                 
 │ Current Startups                 │ Pre-condition cost estimation   │ Reactive, not real-time; no subsidy layer │                                                                                 
 └──────────────────────────────────┴─────────────────────────────────┴───────────────────────────────────────────┘                                                                                 
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 3. Product Vision & Goals                                                                                                                                                                          
                                                                                                                                                                                                    
 ### 3.1. North Star Metric                                                                                                                                                                         
                                                                                                                                                                                                    
 Avg. Out-of-Pocket Cost for Emergency Care ≤ $500 (for 90% of insured + uninsured patients)                                                                                                        
                                                                                                                                                                                                    
 ### 3.2. Secondary Success Metrics                                                                                                                                                                 
                                                                                                                                                                                                    
 - % of eligible patients receiving automatic subsidies                                                                                                                                             
 - Provider adoption rate (contracts signed)                                                                                                                                                        
 - False-negative emergency classification rate (< 0.1%)                                                                                                                                            
 - Patient satisfaction score (target: ≥ 4.5/5)                                                                                                                                                     
 - Operational cost per intervention (target: <$1.50)                                                                                                                                               
                                                                                                                                                                                                    
 ### 3.3. Non-Goals                                                                                                                                                                                 
                                                                                                                                                                                                    
 - Retail clinic pricing                                                                                                                                                                            
 - Chronic disease management                                                                                                                                                                       
 - Preventative care subsidies                                                                                                                                                                      
 - International expansion (Year 1)                                                                                                                                                                 
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 4. User Stories & Personas                                                                                                                                                                         
                                                                                                                                                                                                    
 ┌──────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐                                      
 │ Persona                                  │ Story                                                                                                          │                                      
 ├──────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                      
 │ Insured Patient (Age 35, $45k income)    │ "When I went to the ER for chest pain, I knew my max out-of-pocket would be capped at $450 instead of $5,000." │                                      
 ├──────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                      
 │ Uninsured Patient (Age 60, fixed income) │ "The app told me my heart attack care would cost $300, so I went to the ER instead of delaying care."          │                                      
 ├──────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                      
 │ Safety-Net Hospital CFO                  │ "Our charity-care costs dropped 22% because the platform automates the subsidy payout."                        │                                      
 ├──────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                      
 │ State Medicaid Director                  │ "We can prove compliance with the 90% affordability rule using immutable audit logs."                          │                                      
 └──────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘                                      
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 5. Functional Requirements                                                                                                                                                                         
                                                                                                                                                                                                    
 ### 5.1. Core Features                                                                                                                                                                             
                                                                                                                                                                                                    
 ┌──────┬──────────────────────────────┬─────────────────────────────────────────────────────┬──────────┐                                                                                           
 │ ID   │ Feature                      │ Description                                         │ Priority │                                                                                           
 ├──────┼──────────────────────────────┼─────────────────────────────────────────────────────┼──────────┤                                                                                           
 │ F-01 │ Real-Time Urgency Classifier │ Determines if an encounter is routine vs. emergency │ P0       │                                                                                           
 ├──────┼──────────────────────────────┼─────────────────────────────────────────────────────┼──────────┤                                                                                           
 │ F-02 │ Affordability Engine         │ Calculates max patient cost using income proxy      │ P0       │                                                                                           
 ├──────┼──────────────────────────────┼─────────────────────────────────────────────────────┼──────────┤                                                                                           
 │ F-03 │ Subsidy Orchestrator         │ Triggers automated payments to provider             │ P0       │                                                                                           
 ├──────┼──────────────────────────────┼─────────────────────────────────────────────────────┼──────────┤                                                                                           
 │ F-04 │ Provider API                 │ Allows EHRs to push encounter data                  │ P0       │                                                                                           
 ├──────┼──────────────────────────────┼─────────────────────────────────────────────────────┼──────────┤                                                                                           
 │ F-05 │ Patient App                  │ Mobile UI for cost estimate & subsidy status        │ P1       │                                                                                           
 ├──────┼──────────────────────────────┼─────────────────────────────────────────────────────┼──────────┤                                                                                           
 │ F-06 │ Audit Ledger                 │ Immutable record of every classification/payment    │ P0       │                                                                                           
 ├──────┼──────────────────────────────┼─────────────────────────────────────────────────────┼──────────┤                                                                                           
 │ F-07 │ Provider Dashboard           │ Real-time subsidy reconciliation & analytics        │ P1       │                                                                                           
 └──────┴──────────────────────────────┴─────────────────────────────────────────────────────┴──────────┘                                                                                           
                                                                                                                                                                                                    
 ### 5.2. Non-Functional Requirements                                                                                                                                                               
                                                                                                                                                                                                    
 ┌──────┬──────────────────────────┬───────────────────────────────────┐                                                                                                                            
 │ ID   │ Requirement              │ Target                            │                                                                                                                            
 ├──────┼──────────────────────────┼───────────────────────────────────┤                                                                                                                            
 │ N-01 │ Latency (Classification) │ < 150ms p99                       │                                                                                                                            
 ├──────┼──────────────────────────┼───────────────────────────────────┤                                                                                                                            
 │ N-02 │ HIPAA Compliance         │ End-to-end encryption, audit logs │                                                                                                                            
 ├──────┼──────────────────────────┼───────────────────────────────────┤                                                                                                                            
 │ N-03 │ Uptime                   │ 99.9% SLA                         │                                                                                                                            
 ├──────┼──────────────────────────┼───────────────────────────────────┤                                                                                                                            
 │ N-04 │ Data Residency           │ US-only processing                │                                                                                                                            
 └──────┴──────────────────────────┴───────────────────────────────────┘                                                                                                                            
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 6. Technical Architecture (High-Level)                                                                                                                                                             
                                                                                                                                                                                                    
 ### 6.1. System Context Diagram                                                                                                                                                                    
                                                                                                                                                                                                    
 ```mermaid                                                                                                                                                                                         
   graph TD                                                                                                                                                                                         
       A[Patient] --> B((Mobile App))                                                                                                                                                               
       C[Hospital EHR] --> D((Provider API))                                                                                                                                                        
       D --> E[Vault / KMS]                                                                                                                                                                         
       E --> F[Ingestion Gateway]                                                                                                                                                                   
       F --> G[Kafka/NATS]                                                                                                                                                                          
       G --> H[Urgency Classifier]                                                                                                                                                                  
       H --> I[Economic Engine]                                                                                                                                                                     
       I --> J((Payment Rails))                                                                                                                                                                     
       I --> K((Audit Ledger))                                                                                                                                                                      
       L[Gov/Insurer] --> M((Subsidy Pool))                                                                                                                                                         
       M --> I                                                                                                                                                                                      
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 ### 6.2. Key Components                                                                                                                                                                            
                                                                                                                                                                                                    
 - Ingestion Gateway: Protobuf-based, mTLS-authenticated                                                                                                                                            
 - Urgency Classifier: Ensemble of rule engine + encrypted ML model in Nitro Enclave                                                                                                                
 - Economic Engine: Temporal.io workflows for subsidy orchestration                                                                                                                                 
 - Audit Ledger: Amazon QLDB for immutable compliance trail                                                                                                                                         
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 7. Data Model (Simplified)                                                                                                                                                                         
                                                                                                                                                                                                    
 ```sql                                                                                                                                                                                             
   CREATE TABLE patient_profiles (                                                                                                                                                                  
       patient_pseudo_id UUID PRIMARY KEY,                                                                                                                                                          
       income_bracket_id INT REFERENCES income_brackets(id),                                                                                                                                        
       enrolled_at TIMESTAMP                                                                                                                                                                        
   );                                                                                                                                                                                               
                                                                                                                                                                                                    
   CREATE TABLE income_brackets (                                                                                                                                                                   
       id SERIAL PRIMARY KEY,                                                                                                                                                                       
       min_annual_cents BIGINT,                                                                                                                                                                     
       max_annual_cents BIGINT,                                                                                                                                                                     
       affordability_cap_multiplier NUMERIC DEFAULT 0.10                                                                                                                                            
   );                                                                                                                                                                                               
                                                                                                                                                                                                    
   CREATE TABLE urgency_events (                                                                                                                                                                    
       event_id UUID PRIMARY KEY,                                                                                                                                                                   
       patient_pseudo_id UUID REFERENCES patient_profiles(patient_pseudo_id),                                                                                                                       
       provider_id UUID,                                                                                                                                                                            
       cpt_code TEXT,                                                                                                                                                                               
       icd10_code TEXT,                                                                                                                                                                             
       vitals JSONB,                                                                                                                                                                                
       classification_final TEXT CHECK (classification_final IN ('ROUTINE', 'EMERGENCY')),                                                                                                          
       affordability_cap_cents BIGINT,                                                                                                                                                              
       patient_payment_cents BIGINT,                                                                                                                                                                
       subsidy_amount_cents BIGINT,                                                                                                                                                                 
       status TEXT CHECK (status IN ('PENDING', 'SETTLED', 'FAILED')),                                                                                                                              
       created_at TIMESTAMP DEFAULT NOW()                                                                                                                                                           
   );                                                                                                                                                                                               
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 8. Monetization & Business Model                                                                                                                                                                   
                                                                                                                                                                                                    
 ### 8.1. Revenue Streams                                                                                                                                                                           
                                                                                                                                                                                                    
 ┌─────────────────────┬──────────────────────────────────────────┬───────────────────────┐                                                                                                         
 │ Stream              │ Description                              │ Target Margin         │                                                                                                         
 ├─────────────────────┼──────────────────────────────────────────┼───────────────────────┤                                                                                                         
 │ Provider SaaS Fee   │ Monthly SaaS fee per provider            │ $2,500/provider/month │                                                                                                         
 ├─────────────────────┼──────────────────────────────────────────┼───────────────────────┤                                                                                                         
 │ Transaction Fee     │ 0.25% on subsidy payouts                 │ $0.25 per transaction │                                                                                                         
 ├─────────────────────┼──────────────────────────────────────────┼───────────────────────┤                                                                                                         
 │ State/Gov Contracts │ Annual contract for Medicaid integration │ $5M/yr initial pilot  │                                                                                                         
 └─────────────────────┴──────────────────────────────────────────┴───────────────────────┘                                                                                                         
                                                                                                                                                                                                    
 ### 8.2. Cost Structure                                                                                                                                                                            
                                                                                                                                                                                                    
 - AWS/GCP cloud (HIPAA-compliant)                                                                                                                                                                  
 - KMS/Vault for encryption                                                                                                                                                                         
 - ML model training & maintenance                                                                                                                                                                  
 - Legal/compliance overhead                                                                                                                                                                        
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 9. Roadmap & Milestones                                                                                                                                                                            
                                                                                                                                                                                                    
 ┌─────────┬─────────────────────────────────────────────────────────────────────────────┐                                                                                                          
 │ Quarter │ Milestone                                                                   │                                                                                                          
 ├─────────┼─────────────────────────────────────────────────────────────────────────────┤                                                                                                          
 │ Q1 2026 │ Build MVP classifier + ingestion gateway; pilot with 2 safety-net hospitals │                                                                                                          
 ├─────────┼─────────────────────────────────────────────────────────────────────────────┤                                                                                                          
 │ Q2 2026 │ Launch Patient Mobile App + Provider Dashboard                              │                                                                                                          
 ├─────────┼─────────────────────────────────────────────────────────────────────────────┤                                                                                                          
 │ Q3 2026 │ Integrate with 3 state Medicaid systems                                     │                                                                                                          
 ├─────────┼─────────────────────────────────────────────────────────────────────────────┤                                                                                                          
 │ Q4 2026 │ Expand to 50+ providers; publish peer-reviewed outcome study                │                                                                                                          
 └─────────┴─────────────────────────────────────────────────────────────────────────────┘                                                                                                          
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 10. Risks & Mitigations                                                                                                                                                                            
                                                                                                                                                                                                    
 ┌───────────────────────────────────────────┬────────┬────────────────────────────────────────────────────────┐                                                                                    
 │ Risk                                      │ Impact │ Mitigation                                             │                                                                                    
 ├───────────────────────────────────────────┼────────┼────────────────────────────────────────────────────────┤                                                                                    
 │ Regulatory pushback (CMS/HIPAA)           │ High   │ Pre-file SaMD logic with FDA; publish whitepaper       │                                                                                    
 ├───────────────────────────────────────────┼────────┼────────────────────────────────────────────────────────┤                                                                                    
 │ Model bias (under-triage minority groups) │ High   │ Stratified training dataset; quarterly fairness audits │                                                                                    
 ├───────────────────────────────────────────┼────────┼────────────────────────────────────────────────────────┤                                                                                    
 │ Provider adoption friction                │ Medium │ Offer free 90-day trial; dedicated onboarding team     │                                                                                    
 ├───────────────────────────────────────────┼────────┼────────────────────────────────────────────────────────┤                                                                                    
 │ Exchange-rate risk (crypto subsidy)       │ Low    │ Use stablecoins only; hedge via DeFi protocols         │                                                                                    
 └───────────────────────────────────────────┴────────┴────────────────────────────────────────────────────────┘                                                                                    
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 11. Appendices                                                                                                                                                                                     
                                                                                                                                                                                                    
 - A1: Detailed ML Training Dataset Schema                                                                                                                                                          
 - A2: Provider Integration API Specification (OpenAPI 3.1)                                                                                                                                         
 - A3: Legal Opinion on State vs Federal Jurisdiction                                                                                                                                               
 - A4: Cost-Benefit Analysis (2026–2030 projections)       