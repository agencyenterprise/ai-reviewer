Supplementary Materials for

Emissions and energy impacts of the Inflation Reduction Act

John Bistline et al.

Corresponding author: John Bistline, jbistline@epri.com

Science 380, 1324 (2023)
DOI: 10.1126/science.adg3781

The PDF file includes:

Materials and Methods S1 to S7
Figs. S1 to S26
Tables S1 to S6
References

1

Acknowledgments
The views and opinions expressed in this paper are those of the authors alone and do not necessarily represent those
of their respective institutions, the U.S. Department of Energy (DOE), the U.S. Government, or other funding
agencies, and no official endorsement should be inferred. The authors thank Jordan Wingenroth for his assistance
with social cost of CO2 data.

Funding
J.F., J.J., R.J., E.M., N.P., and G.S. were funded by the William and Flora Hewlett Foundation. B.K., H.K., and J.L.
were funded by Bloomberg Philanthropies, the William and Flora Hewlett Foundation, and the Heising-Simons
Foundation. H.M and A.Z. were funded by Bloomberg Philanthropies. R.W. was funded by Lawrence Berkeley
National Laboratory under Contract No. DE-AC02-05CH11231 with the US DOE. M.B., A.H., and D.S. were
funded by the DOE Office of Policy through the National Renewable Energy Laboratory, operated by Alliance for
Sustainable Energy, LLC, for the DOE under Contract No. DE-AC36-08GO28308.

Competing Interests
Jesse Jenkins is part owner of DeSolve, LLC, which provides techno-economic analysis and decision support for
clean energy technology ventures and investors. A list of clients can be found at
https://www.linkedin.com/in/jessedjenkins. He serves on the advisory boards of Eavor Technologies Inc., a closed-
loop geothermal technology company, and Rondo Energy, a provider of high-temperature thermal energy storage
and industrial decarbonization solutions and has an equity interest in both companies. He also provides policy
advisory services to Clean Air Task Force, a non-profit environmental advocacy group, and serves as a technical
advisor to MUUS Climate Partners and Energy Impact Partners, both investors in early-stage climate technology
companies. Ryan Wiser is a senior scientist at Lawrence Berkeley National Laboratory, on partial detail under
contract to the U.S. Department of Energy. The other authors declare no competing interests.

2

Materials and Methods

S1: Participating Energy-Economic Models

The nine-model intercomparison includes a wide range of independent, state-of-the-art

models. These models capture complicated economic and energy system interactions of the
Inflation Reduction Act (IRA) and other policies. Model intercomparisons are used in a variety
of fields to identify robust insights and potential areas of uncertainty (1).

Models in the study vary in their coverage and structure. Three models are partial
equilibrium models that focus on the power sector, while the other six models represent broader
energy systems. Power sector models can provide additional temporal, spatial, and technological
detail for system operations and investments, while energy system models capture linkages with
broader systems and the economy, including cross-sector interactions that are amplified by
IRA’s end-use electrification incentives. Table S2 and Table S3 compare key model features and
provide links to detailed documentation. Table S4 and Table S5 compare model representations
of emerging technologies and expansion constraints.

The nine participating models are:

•  EPS-EI: The Energy Policy Simulator (EPS) is a forward-simulating, annual timestep,
single-region model, developed by Energy Innovation LLC, which aims to provide
information about which climate and energy policies will reduce GHG emissions most
effectively and at the lowest cost. It includes every major sector of the economy:
transportation, electricity supply, buildings, industry, agriculture, and land use. The EPS
takes outputs from other publicly available models and studies, such as the U.S. Energy
Information Administration’s Annual Energy Outlook, to create a business-as-usual
scenario. When users select policies, the model tracks changes from the business-as-usual
projections to estimate how policy affects energy demand and costs, among other outputs.

•  GCAM-CGS: GCAM-USA-AP is a special purpose fork of the Global Change Analysis

Model (GCAM) version 5.3, utilized and maintained by the Center for Global
Sustainability. GCAM-USA-AP follows the standard release of GCAM 5.3, but also adds
detailed representations of sector-specific climate policies at the state level (2). GCAM
tracks emissions of 16 different species of GHGs and air pollutants from energy,
agriculture, land use, and other industrial systems. The energy system formulation in
GCAM consists of detailed representations of depletable primary sources such as coal,
gas, oil, and uranium, in addition to renewable resources such as bioenergy, hydropower,
wind, and geothermal. These energy resources are processed and consumed by end users
in the buildings, transportation, and industrial sectors. GCAM is a hierarchical market
equilibrium model. The equilibrium in each period is solved by finding a set of market
prices such that supplies and demands are equal in all simulated markets (3).

•  Haiku-RFF: Resources for the Future’s Haiku model is a system operation and capacity
planning model of the U.S. electricity sector. With perfect foresight across a 26-year time
horizon, it finds the least-cost way to meet electricity sector demand in each of the
transmission-constrained 48 contiguous states and D.C., with representation of state-level
market characteristics and technology mandates and emissions caps. System operation
within each year is broken into three seasons with eight time blocks each. Fuel costs, load
shapes, declining technology costs, and rising demand are exogenous.

3

•  IPM-NRDC: The Integrated Planning Model (IPM) is a multi-regional, dynamic, and

deterministic linear programming model of the U.S. electric power sector. IPM optimizes
for the least-cost pathway available for the construction, economic retirement, and use of
power plants, subject to resource adequacy requirements and environmental constraints.
It is used by the U.S. Environmental Protection Agency (EPA) for regulatory impact
assessments of power sector regulations, as well as by state agencies and the Regional
Greenhouse Gas Initiative. It is a proprietary model of ICF.

•  MARKAL-NETL: MARKAL is a bottom-up, dynamic, linear programming

optimization model that finds the cost-optimal pathway within the context of the entire
energy system. MARKAL does not contain an in-built database, so in this study, the
publicly available EPAUS9r2017 database for the U.S. energy system has been adopted
and modified by the National Energy Technology Laboratory (NETL). MARKAL-NETL
represents U.S. Census regions from 2010-2075 with five-year time periods. Each of the
nine regions is modeled as an independent energy system with different regional costs,
resource availability, existing capacity, and end-use demands. Regions are connected
through a trade network that allows transmission of electricity and transport of gas and
fuels. Electricity transmission is constrained to reflect existing regional connections
between North American Electric Reliability Corporation regions as closely as possible.
MARKAL-NETL represents energy imports and exports, domestic production of fuels,
fuel processing, infrastructures, secondary energy carriers, end-use technologies, and
energy service demands of the entire economy.

•  NEMS-RHG: RHG-NEMS is a version of the Energy Information Administration’s

National Energy Modeling System (NEMS) modified by Rhodium Group. RHG-NEMS
is comprised of 13 modules providing energy sector-wide coverage on the supply and
demand side as well as macroeconomic interactions and interactions with global energy
markets. The supply-side modules generally rely on least-cost optimization, while the
demand-side modules are a combination of least-cost optimization and other consumer
adoption modeling approaches. Outside of NEMS, which provides energy CO2
projections, Rhodium Group applies an in-house model to project the additional GHGs
targeted for reduction under the Kyoto Protocol. Regionality, temporal resolution, and
technology representation vary across modules.

•  ReEDS-NREL: The U.S. Department of Energy National Renewable Energy

Laboratory’s Regional Energy Deployment System (ReEDS) is a publicly available,
bottom-up representation of the U.S. electricity sector. In the setup for this study, the
linear program portrays electricity supply and demand as well as the provision of
operating reserves for grid reliability at 134 different balancing areas while also
representing 356 sub-regions where variable renewable capacity can be built. The Augur
sub-module solves hourly dispatch across multiple load years to estimate capacity credit
and curtailment.

•  REGEN-EPRI: The U.S. Regional Economy, Greenhouse Gas, and Energy (REGEN)
model is developed and maintained by the Electric Power Research Institute (EPRI).
REGEN links a detailed power sector planning and dispatch model with an energy end-
use model (4). The power sector model simultaneously finds cost-minimizing pathways
for capacity investments, transmission expansion, and dispatch. The model features
hourly resolution to capture the evolving end-use mix and a representative hour approach

4

for power sector investment and operations. The end-use model captures technology
choices at the customer level with differences across model regions, sectors, and
structural classes.

•  RIO-REPEAT: The Regional Investment and Operations Model (RIO) supply-side

model and EnergyPATHWAYS demand-side model were developed by Evolved Energy
Research. The models provide detailed energy accounting and examine optimal energy
system investment and operations. The tools have high resolution across sectors of the
economy (more than 60 U.S. energy system subsectors), time (annual turnover of
equipment stocks coupled with an hourly electricity-dispatch model), and geography (16
different regions of the United States along with the transmission connecting them). The
modeling tools are employed to conduct a rigorous technical quantification of the
infrastructure upgrades and technology investments needed across all sectors of the
energy system, including cross-sectoral opportunities, to achieve both near- and long-
term climate goals while meeting projected demand for energy services.

Results in the text compare outputs across these nine models in terms of ranges and mean values,
which offer rough indications of variation across models as well as measures of central tendency.
However, it is important to bear in mind that comparisons across models, much like scenario
ensembles, should not be interpreted as statistical samples or as indications of the likelihoods of
particular outcomes (5). Model results are not distributions and only provide an ad hoc
representation of uncertainty, as the full uncertainty is likely to be larger than the range suggests
(e.g., due to structural uncertainties associated with models as well as parametric uncertainties
associated with future technologies, policies, and markets).

Model outputs should not be interpreted as predictions of policy-induced changes for

several reasons. First, models vary in their coverage and implementation of IRA provisions
(Table S1), as described in SM S2. The bill’s complexity and pending guidance from
government agencies require subjective judgments from modeling teams. Second, there is
considerable uncertainty about technological change, policies, inflationary trends, domestic
macroeconomic environment, and global drivers. Policy and technological change, which IRA
may amplify, are particularly uncertain. Third, models vary in their scope and resolution, which
may impact energy system and emissions outcomes. For instance, the literature indicates that
model choices related to temporal and spatial resolution are linked to renewables and energy
storage deployment (6; 7). While power sector impacts are explored with both economy-wide
and power-sector-only models alike, impacts outside of the power sector are not evaluated with
detailed sectoral models to understand how increased resolution may alter modeled outcomes.

S2: Scenario Design

IRA scenarios represent central estimates of core climate and energy provisions of each
respective model. Models vary in their coverage and implementation of IRA provisions (Table
S1). The core modeled provisions are expected to capture the majority of IRA’s impacts, even
though many provisions are not explicitly represented. Economy-wide and power sector models
all include core extensions and enhancements of power-sector-related tax credits, including
production tax credits (PTC), investment tax credits (ITC), and credits for captured CO2 (45Q).
Note that Table S1 is not an exhaustive list of IRA provisions, some of which are modeled while
others are not. Eligibility requirements for tax credit bonuses aim to encourage high-road jobs,

5

increase deployment of low-emitting technologies in low-income/energy, and spur domestic
manufacturing. Many models assume that labor bonuses are met and that some technology-
specific share of projects qualify for other bonuses.

To understand effects on emissions and energy systems, IRA scenarios are compared to

their counterfactual reference scenarios without IRA but including other current federal and state
policies, regulations, and incentives. Many models incorporate on-the-books policies in this
benchmark scenario up through early 2022 such as:

•  The Infrastructure Investment and Jobs Act

•  Federal ITC, PTC, and 45Q with phase outs

•  State-level clean electricity standards and renewable portfolio standards, including
technology-specific carveouts and mandates (e.g., energy storage, offshore wind)

•  Regional- and state-level emissions policies, including economy-wide policies (e.g.,

California’s cap-and-trade) and power sector CO2 caps (e.g., the Regional Greenhouse
Gas Initiative)

•  Federal and state performance standards for end-use technologies

These reference scenarios generally do not include proposed but not yet final regulations,
including EPA’s proposed methane rule and others.

This model intercomparison does not harmonize other technology, market, and policy

assumptions, which means that models use their native input assumptions for technological
costs.1 Input assumptions for capital costs of key power sector resources are shown over time in
Fig. S1.2 Many models assume exogenous technological change, including reductions in capital
costs of generation and energy storage options (Fig. S1).3 Models broadly align in their trends of
these technologies, and values over time generally fall in the range of the National Renewable
Energy Laboratory’s Annual Technology Baseline, which several use for their input assumptions.
Table S4 compares model representations of emerging technologies, including carbon capture
and storage (CCS), hydrogen, and carbon removal.4 Table S5 provides model-specific
assumptions about deployment constraints across different technologies. Many models include
constraints on the near-term deployment on technologies with longer lead times (e.g.,
transmission, nuclear) over the next few years.

There is greater variation in natural gas prices across models (Fig. S2). This range reflects

uncertainty about how prices of fossil fuels will change over time, especially given near-term
inflationary drivers and the Russo-Ukrainian war.

S3: IRA Background

IRA is challenging to model due to its scope and complexity. The policy design of IRA
through tax incentives, grants, loans, and rebates does not necessarily guarantee a fixed amount
of emissions reductions or a price on emissions that encourages lowest marginal abatement cost

1 Harmonization can isolate policy effects but does not capture the coevolution and impacts of policy, market, and
technology drivers that could affect IRA performance.
2 Monetary values are expressed in 2020 U.S. dollars unless otherwise noted.
3 EPS-EI and NEMS-RHG include endogenous technological learning.
4 All models generally include electricity generation options such as solar, wind, and natural-gas-fired capacity.

6

opportunities. Unlike standards or emissions caps, IRA’s investment-based climate policy
approach does not target specific outcomes but instead provides an extension and expansion of
previous investment-centered approaches.5 In other words, IRA changes the relative prices of
fuels and end-use equipment by making lower-emitting resources lower cost, but does not
directly price carbon or cap emissions. Variation in IRA implementation across models is also
caused by the bill’s complexity and elements that require guidance from government agencies.

Updates to power sector tax credits include extending their timeline and value (e.g.,

increasing 45Q credits for captured and stored CO2 from $50/t-CO2 to $85/t-CO2), expanding
their eligibility (e.g., making the ITC and PTC technology-neutral, allowing standalone energy
storage to claim the ITC) and flexibility (e.g., allowing technologies to claim the ITC or PTC,
depending on which is more lucrative in their specific circumstances), adding bonus credits (e.g.,
for energy communities and domestic content), and improving access (e.g., direct pay for
nonprofits and tax-exempt utilities and making credits transferrable for others). Tax equity
market assumptions in models appear as reductions in effective ITC and PTC values. Future tax
credit values are generally assumed to be indexed for inflation.

These complexities make modeling IRA challenging relative to earlier decarbonization

policies and proposals. There is also considerable uncertainty in terms of how IRA could unfold
and a range of possible outcomes based on different interpretations of its provisions (SM S7).
Additionally, the dependence of several decarbonization pathways on infrastructure expansion—
electricity transmission, hydrogen infrastructure, CO2 pipelines, and others—raises questions
about permitting and the degree to which such infrastructure may limit or accelerate technology
adoption. Table S4 compares model representations of emerging technologies and their
associated infrastructure, while Table S5 summarizes model-specific expansion constraints. Note
that the IRA scenarios in the main text focuses on central estimates of climate and energy
provisions. However, uncertainty about IRA implementation, combined with uncertainties about
external factors, implies that ranges for outcomes of interest may be broader than the values in
the main text.

S4: Emissions Results

Fig. S5B shows the sectoral emissions reductions under IRA scenarios relative to 2005,

with Fig. S3 showing 2030 emissions levels in this scenario.6 For non-CO2 GHGs, note that
Carbon Dioxide Equivalence (CO2e) calculations use 100-year Global Warming Potential
(GWP) values from IPCC’s Fourth Assessment Report (AR4) to be consistent with the UNFCCC
reporting requirements. Waterfall diagrams for individual models in Fig. S4 show emissions
reductions from IRA relative to 2005 levels and the resulting emissions gap to reach 50%
reductions by 2030. This emissions gap is 1.0-1.6 Gt-CO2e/yr in the reference scenario and
reduces to 0.5 to 1.1 Gt-CO2e/yr with IRA.

Sectoral emissions reductions relative to the reference from IRA are shown in Fig. 1B. In

2025, most models indicate a reduction in emissions from IRA relative to the reference.
However, a third of models exhibit an increase in power sector emissions in 2025 with IRA,

5 Revenue from IRA comes from adjusting the minimum tax rate for corporations, taxing stock buybacks, enforcing
existing taxes, and negotiating Medicare drug prices. Participating models do not represent potential feedbacks from
these tax reforms.
6 Emissions changes are relative to self-reported 2005 baselines to better harmonize reporting categories.

7

since models are no longer front-loading wind and solar investments to take advantage of
expiring tax credits. By 2030 (2035), IRA decreases emissions by 190-990 Mt-CO2e (560-1,140
Mt-CO2e) annually below the reference for the economy-wide models. Fig. 1 in the main text
compares differences in economy-wide emissions between the IRA and reference scenarios over
time, indicating that differences in 2030 emissions reductions are not solely due to differences in
reference levels in 2030.

Power sector emissions over time are shown in Fig. S7 under the reference and IRA

scenarios. The bottom panel of this figure illustrates the percentage point difference between the
IRA and reference scenarios. IRA lower power sector emissions by 5-34 p.p. in 2030 and 13-36
p.p. in 2035. The scatter plot in Fig. S8 compares model-specific reductions in the reference and
IRA scenarios and suggests that model responsiveness to IRA incentives is not driven primarily
by different reference scenarios. Wind and solar deployment, fossil fuel declines, and other
trends under the baseline play some role in IRA projections, but other factors including model
structure (e.g., temporal resolution,7 financing, foresight in Table S3) and input assumptions
(e.g., technological costs in Fig. S1, natural gas prices in Fig. S28) are also influential in cross-
model variation in emissions and clean energy deployment. This figure also illustrates how IRA
outcomes narrow through 2035 relative to 2030, largely due to models with lower abatement by
2030 nearing the other models by 2035.

One study estimates that net 2030 emissions increases from the oil and gas leasing

provisions in IRA are unlikely to exceed 50 Mt-CO2/yr (8). Even with this conservative
assumption, for every ton of emissions increase from oil and gas provisions, there would be as
much as 18 tons of emissions abated through other IRA provisions.

Climate benefits calculations in Fig. S10 are based on social cost of CO2 distributions
from the GIVE model in Rennert, et al. (2022) (9). Distributions for the social cost of CO2 by
discount rate are shown in Fig. S9 and are based on Resources for the Future Socioeconomic
Projections (RFF-SP) scenario samples with uncertainty in climate model, sea-level model, and
climate damage parameters. These values are multiplied by the difference in 2030 emissions with
and without IRA (Fig. S5) to estimate the distribution of climate benefits, which represents
reduced societal damages associated with agriculture, mortality, sea-level rise, energy
consumption, and other impacts. Note that Fig. S10 indicates which models include only the
electric sector so that their generally lower climate benefits can be attributed to their limited
scope (rather than to their more limited emissions reductions). The full distribution of damage
estimates in Fig. S10 imply a broad range of climate benefits.

Fig. S11 compares distributions of social cost of CO2 estimates in 2030 with average
abatement costs across models. These calculations take net changes in energy system costs in
2030 relative to the reference without IRA—including energy costs (Fig. S19), tax credits (Fig.
S21), capital costs of supply- and demand-side technologies, and maintenance—and divide these
costs by emissions reductions from IRA in 2030 (i.e., the difference between GHG emissions in
the IRA case and the reference without IRA, Fig. S5). Incentives can deliver benefits far into the

7 Temporal resolution refers to the number of intra-annual periods represented for electric sector investment and
dispatch decisions, which are compared across models in Table S2. Earlier research indicates that the number of
intra-annual timeslices and their selection can materially alter model assessments of the economics of power sector
decarbonization (20).
8 Several models assume lower natural gas price trajectories than recent levels. If higher prices persisted, regional
natural gas shares and decarbonization would shift, potentially increasing reference decarbonization rates and
reducing incremental impacts of IRA tax credits (21; 22).

8

future by lowering operating costs of the energy system, so incorporating these longer time
horizons to measure the savings would decrease abatement costs. Note that cost-effectiveness
calculations use undiscounted costs for comparability with Joint Committee on Taxation (JCT)
and Congressional Budget Office (CBO) values.9 There are several other caveats to bear in mind
in comparing average abatement costs with social cost of CO2 estimates, including the omission
of other co-benefits (e.g., improved air quality), the possible divergence between average and
marginal costs,10 and the exclusion of deadweight losses from market distortions.

Average abatement costs across models range from $27-102/t-CO2 with an average of
$61/t-CO2 all models. Economy models have higher abatement costs ($71/t-CO2 average) than
electric sector models ($57/t-CO2 average), given the cost-effectiveness of power sector tax
credits vis-à-vis non-electric incentives under IRA. In part, abatement costs are higher for some
end-use credits owing to the fraction of inframarginal transfers to households that would have
adopted these IRA-supported technologies even without tax credits (e.g., electric vehicles in Fig.
S14). Even with these transfers and higher fiscal costs (Fig. S21, discussed in S5), average
abatement costs of IRA are generally lower than updated social cost of CO2 values across many
assumed near-term discount rates (Fig. S11). This comparison suggests that additional emissions
reductions could be warranted, because mitigation costs are generally below ranges for the social
cost of CO2, even before accounting for improved air quality and other co-benefits.

As GHG emissions decline due to IRA incentives, other forms of air pollution from fossil

fuel combustion also decline. Fig. S12 shows declines in economy-wide and power sector NOx
and SO2 emissions over time.11 These emissions declines continue historical trends, though IRA
scenarios have accelerated reductions relative to the reference without IRA.

S5: End-Use Results

Electricity demand grows 16% on average for energy system models with endogenous

load growth between 2021 and 2030 under IRA (Fig. S17), which is higher than 13% on average
in the reference case. Transportation leads demand growth, though electrification in buildings
and industry also contribute (Fig. S16). The fraction of light-duty vehicle sales coming from EVs
(including both battery electric and plug-in hybrid electric vehicles) increases from over 7% in
2022 to 32-52% of new sales by 2030 with IRA (41% average), compared with 22-43% (31%
average) in the reference (Fig. S14). The $7,500 tax credit may prove restrictive in terms of its
constraints based on domestic content, assembly, as well as price- and income-based eligibility.
The electrified service demand share, stock share, and emissions lag new sales, given the
turnover rate of the existing fleet (Fig. S15). Other transportation represents a growing share of
transport electrification over time (Fig. S17) due in part to the fewer restrictions on credits for
business and commercial vehicles.

IRA leads to declining fossil fuel consumption across most models and fuels relative to

the reference scenario (Fig. S18), though magnitudes vary by model and fuel. The extent of

9 These comparisons also could compare discounted costs (i.e., to reflect the opportunity cost of capital) as well as
discounted emissions (i.e., to reflect discounting of future climate-related benefits).
10 Unlike carbon pricing or other policy instruments, estimating marginal abatement costs with tax credits requires
more than simply reporting the shadow price on the emissions cap constraint (18; 19).
11 Note that we do not use these emissions trajectories as inputs to air quality modeling and then assess changes in
monetized damages across these scenarios. Estimating air quality co-benefits from IRA is an important area for
future work.

9

petroleum reductions depends largely on substitution with electricity in the transport sector. Coal
and natural gas consumption with IRA relative to the reference depend more on power sector
investment and generation outcomes. Coal consumption continues to decline across most
models, though a near-term rebound in coal use occurs for models with higher natural gas price
assumptions and greater CCS deployment.12

IRA tends to lower energy costs for households and businesses due to declines in fossil

fuel consumption and power sector subsidies (Fig. S19). Total economy-wide cost changes vary
by model and over time. Economy-wide models indicate declines in petroleum and natural gas
spending, which can be partially offset by increases in electricity expenditures. There is cross-
model variation in whether IRA increases or decreases total power sector expenditures relative to
a counterfactual reference without IRA. Increases could be due to greater electricity demand
(from fuel switching), while decreases could be from lower electricity prices (due to investments
in subsidized resources). The balance of these effects depends on which tax credits are used (e.g.,
investment credits lower upfront costs, while production credits lower operating costs over the
first decade after an asset comes online), price formation in models, as well as capacity
deployment and timing.

Fig. S20 shows how IRA decreases residential retail electricity prices in 2030 between 1-

8% relative to the reference. Since electricity prices decline across all models, this result
indicates that increased electricity expenditures in Fig. S19 are likely due to increased electricity
demand from electrification. This hypothesis is supported by the fact that the three models
indicating substantial IRA-induced reductions in power sector costs are partial equilibrium
models, which do not account for quantity changes from electrification.

IRA tax credit values are shown in Fig. S21. Initial estimates of IRA funding and federal

budgetary effects by the JCT and CBO between Fiscal Years 2022 and 2031 indicated nearly
$400B for climate- and energy-related programs, including about $270B for power sector, fuels,
and end-use credits (10). The utilization of IRA tax credits across models in this analysis
suggests a broader range of potential tax expenditures, ranging from $330-870B in total by 2030
($510B average) across economy-wide models, which is 1.2-3.2 times the CBO/JCT score for
comparable credits. Large shares of IRA spending are allocated to provisions with uncapped
incentives, including production- and investment-based tax credits. Tax credit values are higher
across many categories and models in this analysis relative to the CBO/JCT estimates, though
transport-related credits13 and 45Q credits for captured CO2 are categories with low CBO/JCT
estimates and potentially large contributions in several models (Fig. S21). The analysis finds
larger budget impacts after 2031 with cumulative spending of $640-1,300B ($910B average) by
2035 due to extensions of power sector tax credits. Additional public spending on advanced
manufacturing and other climate-related incentives are not included in this total. If these
economy-wide tax expenditures were combined with direct expenditures14 in IRA ($121B), total

12 In particular, MARKAL-NETL exhibits an increase in coal consumption due to its high CCS deployment in the
power sector with 45Q credits, which entails parasitic energy penalties relative to coal capacity without CO2 capture.
13 Uncertainty about the magnitude of clean vehicle credits is due not only to unknowns about future electric vehicle
sales but also to uncertainty about the share of vehicles qualifying for critical minerals and battery sourcing
requirements, eligibility restrictions, and whether leased vehicles are exempt from these stringent requirements.
Note that other studies such as Cole, et al. (forthcoming) (17) estimate clean vehicle credits to have budgetary
effects of about $450B through 2031, which is more than an order of magnitude larger than the CBO/JCT score.
14 Direct expenditures include agricultural and forestry projects, energy loans, industrial decarbonization funds,
Green Bank, and several others.

10

fiscal costs over the ten-year budget window would be $450-1,000B ($630B average). There is a
mix across credit types by model, though production tax credits are the largest expenditure
category for many models. Per Fig. S11 and SM S4, average mitigation costs of IRA, including
these expenditures, are generally below ranges for the social cost of CO2. The range of values
across economy-wide and electric sector models reflects both the range of possible technology
adoptions as well as uncertainty about credit eligibility and magnitudes of bonus credits.

IRA could strengthen these areas where the U.S. already has comparative advantages in
geologic storage, fossil fuel resources, and technical expertise. Fig. S22 shows how tax credits
for captured CO2 (45Q) may lead to CCS deployment in the industrial sector, fuel production,
carbon removal, and the power sector. The extent of captured and stored CO2 varies considerably
by model and over time. Total annual volumes of captured CO2 range from 10-350 Mt-CO2/yr in
2030 (150 Mt-CO2/yr average) and 10-810 Mt-CO2/yr in 2035 (280 Mt-CO2/yr average). Fig.
S23 illustrates how tax credits for hydrogen (45V), alongside credits for captured CO2, increase
low-emissions hydrogen production. Hydrogen production shares vary by model, but IRA tax
credits generally increase electrolytic hydrogen and CCS-equipped production.15

IRA manufacturing credits may bolster domestic production of solar modules, wind
turbines, and batteries. Initial estimates suggest that these manufacturing subsidies could displace
demand with domestically sourced products and even switch the U.S. to become a net exporter in
these areas, though other countries may respond with tariffs or WTO challenges (11). Many of
the models in this analysis do not capture these manufacturing credits or represent international
market dynamics (Table S1).

S6: Land Use and Non-CO2 GHG Emissions

Enhancing the U.S. land sink—also referred to as land use, land use change, and forestry

(LULUCF)—and lowering non-CO2 GHG emissions are additional mitigation pathways from
IRA, which can contribute toward the 2030 climate target (12). Fig. S24 shows the net negative
emissions from the U.S. land sink in 2030 across models. The sink ranges from -750 to -850 Mt-
CO2e (-800 Mt-CO2e average). The land sink is larger than reference projections for each model
and is comparable to the 2030 land sink range in the “United States 7th UNFCCC National
Communication, 3rd and 4th Biennial Report” (13), which indicates a land sink between -720
and -860 Mt-CO2e absent additional policies.

IRA also contributes to non-CO2 GHG mitigation. Fig. S24 shows how these emissions

decline under IRA relative to their reference levels. Most of the economy-wide models represent
the Methane Emissions Reduction Program in IRA (Table S1), which includes a methane
emissions fee and financial support to monitor and reduce methane associated with oil and
natural gas systems. Upstream emissions associated with oil and gas also decline due to
decreasing activity in these sectors under IRA (Fig. S18).

S7: Sensitivity Analysis

Given how models vary in their coverage of IRA provisions (Table S1), we conduct a
sensitivity to illustrate how the core provisions that all models capture are the ones driving the

15 Impacts of 45V credits on production and emissions depend in part on Treasury guidance, which was forthcoming
at the time this analysis was conducted.

11

largest energy system and emissions changes. This “IRA Core” scenario turns off the provisions
that not all models capture and includes production, investment, existing nuclear, and captured
CO2 tax credits.16

Fig. S25 compares emissions, capacity additions, and capacity retirements across these

scenarios. Power sector emissions decline 79-87% by 2035 from 2005 levels with scenarios with
full IRA provisions and 75-86% with core IRA provisions only, indicating that the non-core
provisions only lower power emissions by 1-4 percentage points across models. Likewise,
electric sector capacity additions and retirements are similar across the full and core IRA
scenarios, suggesting that changes are driven primarily by the core provisions that all
participating groups model.

We also conduct low and high IRA sensitivities to understand how assumptions about

implementation can alter emissions. These scenarios use alternate assumptions about bonus
credit eligibility, end-use tax credit eligibility, and implementation details while holding all other
assumptions constant (e.g., input assumptions about technological cost and performance).

Emissions reductions across these scenarios are shown in Fig. S26. The range of
emissions outcomes is broader if IRA implementation uncertainties are included. For economy-
wide models, GHG reductions by 2035 with IRA are 43-48% below 2005 levels in the middle
IRA scenarios presented earlier, and this range increases to 38-51% when the low and high
sensitivities are included. The power sector is where the largest changes occur in these
sensitivities—electricity-related emissions reductions with IRA are 66-87% below 2005 by 2035
in the middle IRA scenarios (across all models), which increases to 60-92% across the low,
middle, and high IRA implementation sensitivities. The responsiveness to changes in IRA
implementation varies across models and is asymmetric in some instances between the low and
high sensitivities. Ultimately, the greater inter-model variation across the middle IRA scenarios
relative to intra-model variation across IRA sensitivities underscores the value of model
intercomparison studies in understanding robust insights and possible variation.

16 Specifically, the “IRA Core” scenario omits provisions related to solar in low-income communities, accelerated
depreciation, funds for rural coops, and transmission financing. Some models exclude these provisions, since their
model structures and scopes do not allow these incentives to be explicitly represented. This sensitivity focuses on
the power sector, given how all models capture these provisions and how the electricity sector is the primary area for
IRA-induced emissions reductions.

12

A

)
s
l
e
v
e
L
5
0
0
2
w
o
e
B
%

l

(
s
n
o
i
s
s
i
m
E
e
d
W
-
y
m
o
n
o
c
E

i

0%

-10%

-20%

-30%

-40%

-50%

-60%

Historical

Reference

IRA

2030 U.S. Target: 50 -52% Below 2005

Ref

IRA

0
3
0
2

5
3
0
2

0
3
0
2

5
3
0
2

Max.
Avg.

Min.

G-C
E-E
M-N
R-R
R-E
N-R

G-C
N-R
M-N
E-E
R-E
R-R

2005

2010

2015

2020

2025

2030

2035

)
e
2
O
C
-
t

M

(
e
c
n
e
r
e
f
e
R
m
o
r
f
e
g
n
a
h
C
G
H
G

200

0

-200

-400

-600

-800

-1,000

-1,200

Net

Non-CO2 GHGs

Other CO2
Transport

Buildings

Industry

Electric

Land

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

EPS-EI

GCAM-CGS Haiku-RFF *

IPM-NRDC * MARKAL-

NEMS-RHG ReEDS-NREL *REGEN-EPRI † RIO-REPEAT

NETL

Fig. 1. Cross-model comparison of U.S. emissions reductions under IRA and reference
scenarios from 2005 levels. (A) Historical and projected economy-wide GHG emissions.
Historical emissions and 100-year Global Warming Potential values (for models representing
non-CO2 GHGs) are based on the U.S. EPA’s “Inventory of U.S. Greenhouse Gas Emissions and
Sinks.” (B) Emissions reductions by sector and model over time under IRA scenarios relative to
reference levels. Models with * designate that electric sector IRA provisions only are
represented, and † denotes energy CO2 IRA provisions only. Additional information on
participating models and study assumptions can be found in Materials and Methods S1 and S2.

13

100%

80%

60%

40%

20%

Reference
IRA

Legend

e
g
n
a
R

s
t
l
u
s
e
r

f
o

Min
Mean
Max

Fig. 2. Summary of key indicators for IRA and reference scenarios across models.
Indicators are 2030 electric sector CO2 reductions (% from 2005 levels), 2030 generation share
from low-emitting technologies (%, including renewables, nuclear, and CCS-equipped
generation), 2030 capacity share from low-emitting technologies (% installed nameplate
capacity), 2030 coal generation decline (% from 2021 levels), economy-wide CO2 reduction (%
from 2005 levels), 2030 electric vehicle new sales share (% of new vehicle sold are battery or
plug-in hybrid electric), 2030 electricity share of final energy (%), and 2030 petroleum reduction
(% from 2005 levels). Model-specific values for these metrics are provided in Table S6.

14

Battery (4-Hour)

Land-Based Wind

Solar PV

)

W
k
/
$
0
2
0
2
(

t
s
o
C

l

a
t
i
p
a
C

$2,000

$1,600

$1,200

$800

$400

$0

$2,000

$1,600

$1,200

$800

$400

$0

$2,000

$1,600

$1,200

$800

$400

$0

2020

2025

2030

2035

2020

2025

2030

2035

2020

2025

2030

2035

NGCC

NGCC with CCS

EPS-EI

GCAM-CGS

Haiku-RFF

IPM-NRDC

MARKAL-NETL

NEMS-RHG

ReEDS-NREL

REGEN-EPRI

RIO-REPEAT

NREL 2022 ATB - Con.

NREL 2022 ATB - Mod.

NREL 2022 ATB - Adv.

)

W
k
/
$
0
2
0
2
(

t
s
o
C

l

a
t
i
p
a
C

$2,800

$2,400

$2,000

$1,600

$1,200

$800

$400

$0

$2,800

$2,400

$2,000

$1,600

$1,200

$800

$400

$0

2020

2025

2030

2035

2020

2025

2030

2035

Fig. S1. Capital cost assumptions of key power sector technologies over time by model.
Costs are shown in 2020 U.S. dollars per kilowatt of nameplate capacity (utility-scale solar PV
capacity is shown in kWAC terms).

15

Historical

)
u
t
B
M
M
/
$
0
2
0
2
(
s
e
c
i
r
P
s
a
G

l

a
r
u
t
a
N

$12

$10

$8

$6

$4

$2

$0

EPS-EI

GCAM-CGS

Haiku-RFF

IPM-NRDC

MARKAL-NETL

NEMS-RHG

ReEDS-NREL

REGEN-EPRI

RIO-REPEAT

2005

2010

2015

2020

2025

2030

2035

Fig. S2. Natural gas price assumptions over time by model. Henry Hub prices are shown
where available (or delivered prices to the power sector).

16

10,000

)
e
2
O
C
-
t

M

(

r
o
t
c
e
S
y
b
s
n
o
i
s
s
i
m
E
G
H
G

8,000

6,000

4,000

2,000

0

-2,000

5
0
0
2

1
2
0
2

I

-

E
S
P
E

-

S
G
C
M
A
C
G

*
F
F
R
-
u
k
a
H

i

*
C
D
R
N
M
P

-

I

L
T
E
N
-
L
A
K
R
A
M

-

G
H
R
S
M
E
N

*
L
E
R
N
S
D
E
e
R

-

†

I

-

R
P
E
N
E
G
E
R

History

2030 IRA

T
A
E
P
E
R
O
R

-

I

Net

Non-CO2 GHGs

Other CO2
Transport

Buildings

Industry

Electric

Land

Fig. S3. Cross-model comparison of U.S. GHG emissions by sector under IRA. Historical
emissions and 100-year Global Warming Potential values are based on the U.S. EPA’s
“Inventory of U.S. Greenhouse Gas Emissions and Sinks.” Electric, industry, buildings, and
transport show CO2 only. “Non-CO2 GHGs” includes other GHGs across all sectors. Models
with * designate that electric sector IRA provisions only are represented (CO2 only), and †
denotes energy CO2 IRA provisions only.

17

6,000

5,000

4,000

3,000

2,000

1,000

)
2
O
C
-
t

M

(
s
n
o
i
s
s
i
m
E
2
O
C
y
g
r
e
n
E

0

6,000

5,000

4,000

3,000

2,000

1,000

)
2
O
C
-
t

M

(
s
n
o
i
s
s
i
m
E
2
O
C
y
g
r
e
n
E

0

6,000

5,000

4,000

3,000

2,000

1,000

)
2
O
C
-
t

M

(
s
n
o
i
s
s
i
m
E
2
O
C
y
g
r
e
n
E

0

EPS-EI

GCAM-CGS

6,000

)
2
O
C
-
t

M

(
s
n
o
i
s
s
i
m
E
2
O
C
y
g
r
e
n
E

5,000

4,000

3,000

2,000

1,000

0

Transport

Buildings

Industry

Electric

2005

2021

Electric Industry Buildings Transport

Gap

2030
Target

2005

2021

Electric Industry Buildings Transport

Gap

2030
Target

MARKAL-NETL

NEMS-RHG

6,000

)
2
O
C
-
t

M

(
s
n
o
i
s
s
i
m
E
2
O
C
y
g
r
e
n
E

5,000

4,000

3,000

2,000

1,000

0

Transport

Buildings

Industry

Electric

2005

2021

Electric Industry Buildings Transport

Gap

2030
Target

2005

2021

Electric Industry Buildings Transport

Gap

2030
Target

REGEN-EPRI

RIO-REPEAT

6,000

5,000

4,000

3,000

2,000

1,000

)
2
O
C
-
t

M

(
s
n
o
i
s
s
i
m
E
2
O
C
y
g
r
e
n
E

0

Transport

Buildings

Industry

Electric

Transport

Buildings

Industry

Electric

Transport

Buildings

Industry

Electric

Transport

Buildings

Industry

Electric

2005

2021

Electric Industry Buildings Transport

Gap

2030
Target

2005

2021

Electric Industry Buildings Transport

Gap

2030
Target

Fig. S4. Cross-model waterfall diagrams of energy CO2 emissions under IRA relative to
2005. Panels show model-specific emissions under IRA and the emissions gap (navy bar) to
reach a 50% by 2030 climate target. 2005 values are based on self-reported baseline values.

18

500

0

-500

-1,000

-1,500

-2,000

-2,500

-3,000

-3,500

-4,000

)
e
2
O
C
-
t

M

(
5
0
0
2
m
o
r
f

r
o
t
c
e
S
y
b
s
n
o
i
t
c
u
d
e
R
G
H
G

1
2
0
2

I

-

E
S
P
E

-

S
G
C
M
A
C
G

*
F
F
R
-
u
k
a
H

i

*
C
D
R
N
M
P

-

I

L
T
E
N
-
L
A
K
R
A
M

-

G
H
R
S
M
E
N

*
L
E
R
N
S
D
E
e
R

-

†

I

-

R
P
E
N
E
G
E
R

History

2030 IRA

T
A
E
P
E
R
O
R

-

I

Electric

Industry

Buildings

Transport

Other CO2

Non-CO2 GHGs

Land

Fig. S5. Emissions reductions by sector and model in 2030 under IRA scenarios from 2005
levels. Models with * designate that electric sector IRA provisions only are represented, and †
denotes energy CO2 IRA provisions only.

19

d
n
a
A
R

i

I
e
d
W
-
y
m
o
n
o
c
E
n

i

e
c
n
e
r
e
f
f
i
D

)
.
p
.
p
(
5
0
0
2
m
o
r
f
s
n
o
i
t
c
u
d
e
R
e
c
n
e
r
e
f
e
R

5%

0%

-5%

-10%

-15%

-20%

-25%

-30%

EPS-EI

GCAM-CGS

MARKAL-NETL

NEMS-RHG

REGEN-EPRI

RIO-REPEAT

2020

2025

2030

2035

Fig. S6. Difference in economy-wide GHG emissions reductions between the IRA and
reference scenarios from 2005 levels (in percentage point terms). Differences corresponding
to trajectories over time in Fig. 1A. Note that economy-wide GHG emissions reductions relative
to 2005 are calculated for each model using only the emissions sources (i.e., energy CO2, land
CO2, other CO2, and non-CO2 GHGs) reported for that model, as shown in Fig. S3.

20

A

)
s
l
e
v
e
L
5
0
0
2
w
o
e
B
%

l

(
s
n
o
i
s
s
i
m
E
r
o
t
c
e
S
r
e
w
o
P

0%

-20%

-40%

-60%

-80%

-100%

Historical

Reference

Ref

IRA

IRA

25% of 2022 Emissions

M-N

G-C
H-R*
E-E
R-N*
R-E
I-N*
N-R
H-R*
M-N
R-R
I-N*

N-R
R-E
G-C
R-R
E-E
R-N*

0
3
0
2

5
3
0
2

Max.

Avg.

Min.

2005

2010

2015

2020

2025

2030

2035

B

d
n
a
A
R

I

r
o
t
c
e
S
r
e
w
o
P
n

i

e
c
n
e
r
e
f
f
i
D

)
.
p
.
p
(
5
0
0
2
m
o
r
f
s
n
o
i
t
c
u
d
e
R
e
c
n
e
r
e
f
e
R

5%

0%

-5%

-10%

-15%

-20%

-25%

-30%

-35%

-40%

EPS-EI

GCAM-CGS

Haiku-RFF

IPM-NRDC

MARKAL-NETL

NEMS-RHG

ReEDS-NREL

REGEN-EPRI

RIO-REPEAT

2020

2025

2030

2035

Fig. S7. Cross-model comparison of U.S. power sector emissions reductions under IRA and
reference scenarios. (A) Reductions below 2005 levels. (B) Difference between the IRA and
reference scenarios (in percentage point terms). Historical emissions are based on the U.S. EPA’s
“Inventory of U.S. Greenhouse Gas Emissions and Sinks.” Models with * designate that electric
sector IRA provisions only are represented.

21

)
5
0
0
2
w
o
e
B
%

l

(

2
O
C
r
o
t
c
e
S
r
e
w
o
P
A
R

I

-30%

-40%

-50%

-60%

-70%

-80%

-90%

-90%

-80%

2030

2035

M-N

R-E

I-N*

I-N*

E-E

R-E

N-R

R-R

N-R

H-R*

H-R*

M-N

G-C

G-C

R-N*

R-R

R-N*

E-E

-70%

-60%
Reference Power Sector CO2 (% Below 2005)

-50%

-40%

-30%

Fig. S8. Cross-model comparison of power sector CO2 emissions reductions (relative to
2005 levels) under the reference and IRA scenarios. Individual model results are shown for
2030 and 2035. Models with * designate that electric sector IRA provisions only are represented.

22

2030 Social Cost of CO 2 (2020$ per tonne of CO2)

Fig. S9. 2030 SC-CO2 distributions by discount rate (2020 USD per metric tonne of CO2).
Social cost of CO2 values come from Rennert, et al. (2022). Mean values are shown above each
distribution with near-term average discount rates of 3.0% (purple), 2.5% (teal), 2.0% (green,
preferred specification), and 1.5% (red).

23

A

MARKAL-NETL

REGEN-EPRI†

IPM-NRDC*

Haiku-RFF*

NEMS-RHG

RIO-REPEAT

ReEDS-NREL*

EPS-EI

GCAM-CGS

B

MARKAL-NETL

REGEN-EPRI†

IPM-NRDC*
Haiku-RFF*

RIO-REPEAT †

NEMS-RHG

ReEDS-NREL*

EPS-EI

GCAM-CGS

$0

$100

$200

$300

$400

2030 Climate Beneﬁts (billion $/yr) with 2% Discount Rate

$0

$100

$200

$300

$400

2030 Climate Beneﬁts (billion $/yr) with 3% Discount Rate

Fig. S10. Cross-model comparison of climate benefits of IRA. (A) Avoided climate-related
social costs from IRA in 2030 (billion $ per year). Social cost of CO2 values come from Rennert,
et al. (2022) using a 2% near-term discount rate. (B) Climate benefits using a 3% near-term
discount rate. Models with * designate that electric sector IRA provisions only are represented,
and † denotes energy CO2 IRA provisions only.

24

)
2
O
C
-
t
/
$
(

2
O
C
f
o
t
s
o
C

l

a
i
c
o
S

$800

$700

$600

$500

$400

$300

$200

$100

$0

5-95% Quantile Range

25-75% Quantile Range

Mean

EPA (2022)

EPS-EI

Haiku-RFF *

IPM-NRDC *

NEMS-RHG

ReEDS-NREL *

REGEN-EPRI †

RIO-REPEAT

2
O
C
e
g
a
r
e
v
A

t
s
o
C
t
n
e
m
e
t
a
b
A

1.5%

2.0%

2.5%

3.0%

Near-Term Discount Rate (%)

Fig. S11. Comparison of 2030 social cost of CO2 values and average abatement costs by
model through 2035. Quantile range for social cost of CO2 values come from Rennert, et al.
(2022). Circles show values from EPA (2022) (14). Models with * designate that electric sector
IRA provisions only are represented, and † denotes energy CO2 IRA provisions only.

25

14

12

10

8

6

4

2

)
r
y
/
2
O
S
-
t

M

(
s
n
o
i
s
s
i
m
E
2
O
S

Historical: Economy

Reference

IRA

Historical: Power

0
2005

2015

2025

2035

20

18

16

14

12

10

8

6

4

2

)
r
y
/
x
O
N
-
t

M

(
s
n
o
i
s
s
i
m
E
x
O
N

Historical: Economy

Reference

IRA

Historical: Power

Economy-Wide Emissions

0
2005

2015

2025

2035

Power Sector Emissions

Fig. S12. Cross-model comparison of criteria pollutant emissions by model over time. SO2
and NOx emissions (left and right panels, respectively) are shown across the economy (darker
dashed lines) and for the power sector only (lighter solid lines). Historical values for economy-
wide emissions come from the U.S. EPA’s “Air Pollutant Emissions Trends Data” (link).
Historical values for power sector emissions come from the U.S. EPA’s “Power Plant Emissions
Trends” (link).

26

A

)
r
y
/
W
G
(
e
g
n
a
h
C
y
t
i
c
a
p
a
C

140

120

100

80

60

40

20

0

-20

-40

Storage

Solar

Wind

Gas CCS

Gas

Coal CCS

Coal

Other

Hydro

Nuclear

1950

1960

1970

1980

1990

2000

2010

2020

Low-Emitting (IRA)

Fossil Without CCS

Low-Emitting (Reference)

Average Rate to 2035

%
6
% 8
6
7

%
7
7

%
1
7

%
3
7

%
0
% 7
0
6

%
8
5

%
8
7

%
5
7

%
9
6

%
7
4

%
9
4

%
0
5

%
9
5

%
7
% 5
6
4

%
8
8

%
2
8

%
9
8

%
8
7

%
5
7

%
5
5

%
8
5

%
3
5

%
1
5

%
2
5

%
0
4

B

100%

)

%

(
e
r
a
h
S
n
o
i
t
a
r
e
n
e
G

90%

80%

70%

60%

50%

40%

30%

20%

10%

0%

2021

EPS-EI

GCAM-CGS

Haiku-RFF

IPM-NRDC MARKAL-NETL NEMS-RHG

ReEDS-NREL REGEN-EPRI

RIO-REPEAT

Fig. S13. Comparison of historical and projected power sector outcomes by technology in
the IRA scenarios across models. (A) Additions and retirements—historical and average annual
projections by model through 2035. Solar values are in GWAC terms and include utility-scale and
distributed capacity. Historical values come from Form EIA-860 data.17 (B) Low-emitting
generation shares, including renewables (with biomass), nuclear, and CCS-equipped generation.
Values are shown over time with IRA relative to the reference scenario.

17 EIA-860 data reflect retirements since 2002. Note that additions and retirements of similar capacity can occur in
the same model, which reflects differences in regional compositions (e.g., retiring capacity in some regions but
adding capacity in others), technology compositions within the same fuel category (e.g., natural gas capacity
includes both combined cycles and combustion turbines), as well as instances where replacing existing assets with
newer capacity can lower system costs (e.g., retiring plants where going-forward costs exceed system benefits).

27

)

%

80%

l

(
e
r
a
h
S
s
e
a
S
w
e
N
e
l
c
i
h
e
V
c
i
r
t
c
e
E

l

Biden Administration 2030 Target

60%

40%

20%

Historical

0%

2010

2015

2020

2025

2030

2035

R-R

R-R

R-E

R-E

E-E
E-E
G-C
N-R
N-R
G-C

2030

Max.

Avg.

Min.

A
R

I

e
c
n
e
r
e
f
e
R

Fig. S14. Electric vehicle new sales share of U.S. light-duty cars and trucks across models.
Values include battery electric vehicles and plug-in hybrid electric vehicles. Historical values are
from the International Energy Agency’s “Global EV Outlook 2022” and Argonne National
Laboratory’s “Light Duty Electric Drive Vehicles Monthly Sales Update” through Dec. 2022.

28

)

%

50%

Reference

IRA

l

(
e
r
a
h
S
s
e
a
S
c
i
r
t
c
e
E
0
3
0
2

l

40%

30%

20%

10%

0%

EPS-EI

GCAM-CGS

NEMS-RHG

REGEN-EPRI

RIO-REPEAT

Reference

IRA

)

%

(
e
r
a
h
S
k
c
o
t
S
c
i
r
t
c
e
E
0
3
0
2

l

50%

40%

30%

20%

10%

0%

EPS-EI

GCAM-CGS

NEMS-RHG

REGEN-EPRI

RIO-REPEAT

Fig. S15. Cross-model comparison of electric vehicle shares in 2030. New sales shares (top
panel) and total vehicle stock (bottom panel) for U.S. passenger vehicles are shown for a
reference scenario (“Ref”) and a scenario with IRA incentives (“IRA”).

29

70%

60%

50%

40%

30%

20%

10%

0%

Buildings

Total

Transportation

)

%

(
y
g
r
e
n
E

l

i

a
n
F
f
o
e
r
a
h
S
c
i
r
t
c
e
E

l

1970

1980

1990

2000

2010

2020

2030

Fig. S16. Cross-model comparison of sectoral electrification trends. Electric share of final
energy by sector under IRA scenarios shown on the right (for 2025, 2030, and 2035), where
markers represent individual model results. Historical values come from U.S. EIA’s “State
Energy Data System” (https://www.eia.gov/state/seds/).

30

)
h
W
T
(
d
n
a
m
e
D
y
t
i
c
i
r
t
c
e
E

l

6,000

5,000

4,000

3,000

2,000

1,000

0

Other

Other Transport

Light-Duty Vehicles

Buildings

Industry

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

EPS-EI

GCAM-CGS

Haiku-RFF *

IPM-NRDC * MARKAL-NETL NEMS-RHG ReEDS-NREL * REGEN-EPRI RIO-REPEAT

Fig. S17. Cross-model comparison of electricity demand by sector over time. Unspecified
load is categorized as “Other.” ReEDS-NREL is a power-sector-only model, so exogenous
electricity demand assumptions are shown, which does not include a sectoral breakdown. Models
with * designate that electric sector IRA provisions only are represented.

31

A

Petroleum

Natural Gas

Coal

Historical

Reference

IRA

45

40

35

30

25

20

15

10

5

)
s
d
a
u
q
(
y
g
r
e
n
E
y
r
a
m

i
r
P

45

40

35

30

25

20

15

10

5

)
s
d
a
u
q
(
y
g
r
e
n
E
y
r
a
m

i
r
P

Historical

Reference

IRA

45

40

35

30

25

20

15

10

5

)
s
d
a
u
q
(
y
g
r
e
n
E
y
r
a
m

i
r
P

0
2005

2015

2025

2035

0
2005

2015

2025

2035

B

10

Petroleum

)
s
d
a
u
q
(
y
g
r
e
n
E
y
r
a
m

i
r
P
n

i

.
f
f
i
D

8

6

4

2

0
2020

-2

-4

-6

-8

-10

2025

2030

2035

Natural Gas

2025

2030

2035

10

8

6

4

2

0
2020

-2

-4

-6

-8

-10

)
s
d
a
u
q
(
y
g
r
e
n
E
y
r
a
m

i
r
P
n

i

.
f
f
i
D

10

8

6

4

2

0
2020

-2

-4

-6

-8

)
s
d
a
u
q
(
y
g
r
e
n
E
y
r
a
m

i
r
P
n

i

.
f
f
i
D

Historical

Reference

IRA

2015

2025

2035

0
2005

Coal

2025

2030

2035

EPS-EI

MARKAL-NETL

NEMS-RHG

REGEN-EPRI

GCAM-CGS

Fig. S18. Primary energy from petroleum, natural gas, and coal across models. (A) Values
are shown for the reference scenario (gray) and IRA scenario (orange). Historical values come
from the U.S. EIA’s “Monthly Energy Review.” (B) Model-specific differences in the IRA
scenario relative to the reference.

32

)
r
y
/
$
n
o

i
l
l
i

b
(
e
c
n
e
r
e
f
e
R
m
o
r
f
e
g
n
a
h
C
e
r
u
t
i
d
n
e
p
x
E

60

40

20

0

-20

-40

-60

-80

Petroleum

Natural Gas

Electric

2025 2030 2035 2025 2030 2035 2025 2030 2035 2025 2030 2035 2025 2030 2035 2025 2030 2035

EPS-EI

IPM-NRDC *

NEMS-RHG

ReEDS-NREL *

REGEN-EPRI †

RIO-REPEAT

Fig. S19. Change in economy-wide energy expenditures by fuel and model under IRA
relative to reference levels. Values shown in undiscounted real (2020) dollar terms. Models
with * designate that electric sector IRA provisions only are represented, and † denotes energy
CO2 IRA provisions only.

33

IRA

Reference

REGEN-EPRI

NEMS-RHG

IPM-NRDC*

Haiku-RFF*

EPS-EI

$0

$20

$40

$60

$80

$100

$120

$140

Retail Electricity Prices in 2030 ($/MWh)

Fig. S20. Residential retail electricity prices by model in 2030. Values are shown for the
reference scenario (gray) and IRA scenario (orange). Models with * designate that electric sector
IRA provisions only are represented, and † denotes energy CO2 IRA provisions only.

34

)
$
n
o

i
l
l
i

b
(
s
e
r
u
t
i
d
n
e
p
x
E
x
a
T
e
v
i
t
a
u
m
u
C

l

1,400

1,200

1,000

800

600

400

200

0

Other

Transport

45Q

PTC

ITC

6
2
0
2

1
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

CBO/JCT

EPS-EI

GCAM-CGS Haiku-RFF *

IPM-NRDC * MARKAL-

NEMS-RHG ReEDS-NREL *REGEN-EPRI † RIO-REPEAT

NETL

Fig. S21. Cross-model comparison of cumulative IRA tax credit value by category over
time. Values shown in undiscounted real (2020) U.S. dollar terms. Note that Haiku-RFF, IPM-
NRDC, MARKAL-NETL, and ReEDS-NREL tax credit values are shown for the power sector
only. Models with * designate that electric sector IRA provisions only are represented, and †
denotes energy CO2 IRA provisions only. CBO/JCT estimates come from (10) and are expressed
in nominal terms. Tax credits: ITC, investment tax credit (power sector); PTC, production tax
credit (power sector); 45Q, credits for captured CO2; 45V, credits for hydrogen.

35

)
r
y
/
2
O
C
-
t

M

(

2
O
C
d
e
r
u
t
p
a
C

900

800

700

600

500

400

300

200

100

0

Other Negative Emissions

Industrial CCS

Biofuels with CCS

Hydrogen with CCS

Power: Biomass

Power: Gas

Power: Coal

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

5
2
0
2

0
3
0
2

5
3
0
2

EPS-EI

GCAM-CGS Haiku-RFF *

IPM-NRDC *

MARKAL-
NETL

NEMS-RHG ReEDS-NREL * REGEN-EPRI † RIO-REPEAT

Fig. S22. Captured CO2 for transport and geologic storage under IRA. Captured CO2 is
shown by category, time, and model. The “Other Negative Emissions” category is primarily
direct air capture. Models with * designate that electric sector IRA provisions only are
represented, and † denotes energy CO2 IRA provisions only.

36

)
s
d
a
u
q
(
n
o
i
t
c
u
d
o
r
P
n
e
g
o
r
d
y
H

2.5

2.0

1.5

1.0

0.5

0.0

I

-

E
S
P
E

-

G
H
R
S
M
E
N

L
T
E
N
-
L
A
K
R
A
M

Electrolysis

Bio with CCS

Other CCS

SMR with CCS

SMR

I

-

E
S
P
E

-

G
H
R
S
M
E
N

L
T
E
N
-
L
A
K
R
A
M

T
A
E
P
E
R
O
R

-

I

T
A
E
P
E
R
O
R

-

I

2030 Reference

2030 IRA

Fig. S23. Hydrogen production by technology across models in 2030. Values are shown for
the reference scenario (left) and IRA scenario (right).

37

T
A
E
P
E
R
O
R

-

I

History

2030 IRA

5
0
0
2

1
2
0
2

I

-

E
S
P
E

-

S
G
C
M
A
C
G

L
T
E
N
-
L
A
K
R
A
M

-

G
H
R
S
M
E
N

0

-200

-400

-600

-800

)
e
2
O
C
-
t

M

(
s
n
o
i
s
s
i
m
E
d
n
a
L

-1,000

-1,200

)
e
2
O
C
-
t

M

(
s
n
o
i
s
s
i
m
E
G
H
G
2
O
C
-
n
o
N

1,600

1,400

1,200

1,000

800

600

400

200

0

IRA Scenario

Historical

Ref. Scenario

7NC Low

7NC High

NCS Low

NCS High

IRA Scenario

Historical

7NC

NCS Low

NCS High

Ref. Scenario

2005

2021

EPS-EI

GCAM-CGS NEMS-RHG RIO-REPEAT

History

2030 IRA

Fig. S24. Historical and projected U.S. land sink and non-CO2 GHG emissions. Historical
emissions are based on the U.S. EPA’s “Inventory of U.S. Greenhouse Gas Emissions and
Sinks.” “7NC” lines show low and high sequestration projections from the “United States 7th
UNFCCC National Communication, 3rd and 4th Biennial Report” reference scenarios with
current policies (13). “NCS” lines show low and high sequestration projections from “The Long-
Term Strategy of the United States” report’s National Climate Strategy action scenarios (15).

38

A

)
e
2
O
C
-
t

M

(

r
o
t
c
e
S
y
b
s
n
o
i
s
s
i
m
E
G
H
G

6,000

5,000

4,000

3,000

2,000

1,000

0

-1,000

B

)
r
y
/
W
G
(
e
g
n
a
h
C
y
t
i
c
a
p
a
C

140

120

100

80

60

40

20

0

-20

-40

2021 Ref

IRA
Full

IRA
Core

Ref

IRA
Full

IRA
Core

Ref

IRA
Full

IRA
Core

Ref

IRA
Full

IRA
Core

History

EPS-EI

ReEDS-NREL *

REGEN-EPRI †

RIO-REPEAT

Net

Non-CO2 GHGs

Other CO2
Transport

Buildings

Industry

Electric

Land

Storage

Solar

Wind

Gas CCS

Gas

Coal CCS

Coal

Other

Hydro

Nuclear

2000

2010

2020

Ref IRA
Full

IRA
Core

Ref IRA
Full

IRA
Core

Ref IRA
Full

IRA
Core

Ref IRA
Full

IRA
Core

EPS-EI

ReEDS-NREL *REGEN-EPRI † RIO-REPEAT
Average Rate to 2035

Fig. S25. Cross-model comparison of emissions and power sector outcomes under IRA
sensitivities. (A) 2030 GHG emissions by sector across models and scenarios. (B) Electric sector
capacity additions and retirements—historical and average annual projections by model through
2035. Values are shown for reference scenarios without IRA (Ref), IRA scenarios with all
provisions (IRA Full), and an IRA scenario with core provisions only (IRA Core). Models with *
designate that electric sector IRA provisions only are represented, and † denotes energy CO2
IRA provisions only. See Section S7 for detailed scenario descriptions.

39

)
e
2
O
C
-
t

M

(
5
0
0
2
m
o
r
f

r
o
t
c
e
S
y
b
s
n
o
i
t
c
u
d
e
R
G
H
G

500

0

-500

-1,000

-1,500

-2,000

-2,500

-3,000

-3,500

-4,000

Electric

Industry

Buildings

Transport

Other CO2

Non-CO2 GHGs
Land

1
2
0
2

w
o
L

i

d
M

h
g
H

i

w
o
L

i

d
M

h
g
H

i

w
o
L

i

d
M

h
g
H

i

w
o
L

i

d
M

w
o
L

i

d
M

h
g
H

i

w
o
L

i

d
M

h
g
H

i

w
o
L

i

d
M

h
g
H

i

EPS-EI

GCAM-CGS Haiku-RFF * MARKAL-

ReEDS-NREL *REGEN-EPRI † RIO-REPEAT

NETL

Fig. S26. Emissions reductions by sector and model in 2035 under IRA scenarios from 2005
levels. Low, mid, and high IRA implementation sensitivities are shown (“Mid” cases are shown
in the other figures). Models with * designate that electric sector IRA provisions only are
represented, and † denotes energy CO2 IRA provisions only.

40

Table S1.

Participating models and IRA provisions represented. Section shown in parentheses. Note
that the table is not an exhaustive list of IRA provisions, some of which are modeled while others
are not.18 “Not Applicable” refers to provisions that the current model structure and scope cannot
represent as written.

GCAM-CGS

Haiku-RFF

IPM-NRDC

MARKAL-NETL

NEMS-RHG

ReEDS-NREL

REGEN-EPRI

RIO-REPEAT

 Included
 Not Included
 Not Applicable

EPS-EI

Sector

Electricity

Multi-Sector

Transport

Buildings

Program (Section)

Production tax credit (PTC) extension (13101)
Investment tax credit (ITC) extension (13102)
Solar in low-income communities (13103/13702)
PTC for existing nuclear (13015)
New clean electricity PTC (45Y, 13701) and ITC (48E, 13702)
Accelerated depreciation (13703)
Funds for rural coops (22004)
Transmission financing (50151)
45Q: Extension of credits for captured CO2 (13104)
45V: Production credits for clean hydrogen (13204)
Loan authority for energy infrastructure (50144)
Extension of incentives for biofuels (13201/13202)
Sustainable aviation credit (13203)
Clean vehicle credit (13401)
Credit for previously owned clean vehicles (13402)
Commercial clean vehicle credit (13403)
Alternative refueling property credit (13404)
Clean fuel PTC (13704)
Residential clean energy credit (13302)
Energy efficient commercial building deduction (13303)
Energy efficient home credit (13304)
Home energy efficiency credit (50121)
High efficiency home rebate program (50122)

Industry and Other Extension of advanced energy project credit (13501)
Advanced manufacturing production credit (13502)
Vehicle manufacturing loans/grants (50142/50143)
Advanced industrial facilities (50161)
Low-carbon materials (60503/60504/60506)
Biodiesel, Advanced Biofuels, SAF
Greenhouse Gas Reduction Fund
Oil and gas lease sales
Methane Emissions Reduction Program
Agriculture and forestry provisions

18 Additional energy and climate provisions include (but are not limited to) DOE ($250 billion loan authority) and
USDA ($10+ billion) programs to encourage fossil-to-clean transitions (e.g., 50144, 22004); production-based
manufacturing tax incentives for wind, solar, and battery equipment as well as critical materials (13502); cross-
cutting programs on emissions reductions and clean technology deployment (60103, 60114); and provisions
intended to support clean energy in buildings, industry, and transport (e.g., 13301, 50161, 50142, 50143).

41

Table S2.
Participating models and key features. Temporal resolution refers to the number of intra-annual segments.

Analysis
Abbreviation
EPS-EI

Model(s)

Energy Policy
Simulator (EPS)

Analysis
Institution
Energy
Innovation

Model
Type
Energy
systems

Geographic
Coverage
50 U.S.
states and
D.C.

Spatial
Resolution
Single
national
region

GCAM-CGS

Haiku-RFF

Global Change
Analysis Model for
AP

Haiku Power Sector
Model

UMD-CGS

Energy
systems

States

50 U.S.
states and
D.C.

Electric
sector

Contiguous
U.S.

States

IPM-NRDC

Electric
sector
MARKAL-NETL  MARKet Allocation  NETL DOE  Energy
systems

Integrated Planning
Model

Contiguous
U.S.
Contiguous
U.S.

67 regions

9 Census
regions

Resources
for the
Future
NRDC

NEMS-RHG

Rhodium Group -
National Energy
Modeling System

Rhodium
Group

Energy
systems

50 U.S.
states and
D.C.

Regions
vary by
sector

Temporal
Resolution
Annual for
end use;
seasonal for
electric
Annual for
end use; 4
segments for
electric
24 segments
for electric

24 segments
for electric
Hourly for end
use; 12
segments for
electric
Annual for
end use; 9
segments for
electric
17 segments
for electric

Link

Link

Link

Link

Link

Link

Link

Link

Link

ReEDS-NREL

REGEN-EPRI

Regional Energy
Deployment System
Regional Economy,
Greenhouse Gas,
and Energy

NREL

EPRI

RIO-REPEAT

RIO (supply-side),
EnergyPATHWAYS
(demand-side)

Evolved
Energy
Research
and ZERO
Lab

Electric
sector
Energy
systems

Contiguous
U.S. here
Contiguous
U.S.

Energy
systems

Contiguous
U.S.

42

134
regions
16 regions  Hourly for end

use; 120
segments for
electric

27 regions  Hourly for end

Link

use; 1,080
segments for
energy supply

Table S3.
Model coverage and sectoral approaches. Coverage and equilibrium approach: PE, partial equilibrium; LP, linear program. Electric
sector models are designated with * (others are energy system models, per Table S2).

Analysis
Abbreviation
EPS-EI

GCAM-CGS

Haiku-RFF*

IPM-NRDC*

MARKAL-
NETL
NEMS-RHG

Model(s)

Energy Policy Simulator
(EPS)
Global Change Analysis
Model for AP
Haiku Power Sector
Model
Integrated Planning
Model
MARKet Allocation

Rhodium Group -
National Energy
Modeling System
ReEDS-NREL*  Regional Energy

REGEN-EPRI

RIO-REPEAT

Deployment System
Regional Economy,
Greenhouse Gas, and
Energy
RIO (supply-side),
EnergyPATHWAYS
(demand-side)

Coverage and Equilibrium
Approach
Economy: System dynamics

Electric Model Approach

Transport Model Approach

Recursive dynamic19

Logit choice

Economy: Logit choice

Recursive dynamic

Logit choice

Power sector PE: Least-cost
LP
Power sector PE: Least-cost
LP
Economy: Least-cost LP

Economy: 13 modules with
least-cost LP supply and
consumer adoption demand
Power sector PE: Least-cost
LP
Energy end use: Lagged logit
choice; Electricity: Least-cost
LP
Economy-wide LP

Perfect foresight

Perfect foresight

Perfect foresight

Perfect foresight

N/A

N/A

Least-cost optimization with
expansion constraints
Logit choice

User-defined (recursive used
here)
Perfect foresight

N/A

Logit choice

Perfect foresight

Scenario-based

19 The EPS employs a simplified recursive dynamic capacity expansion model, which includes endogenously calculated changes to demand. For IRA modeling, the
EPS builds on deployment estimates from ReEDS with endogenously calculated elements.

43

Table S4.
Model representations of emerging technologies. CCS, carbon capture and storage; H2, hydrogen; T&S, transport and storage; O&M,
operations and maintenance. Electric sector models are designated with * (others are energy system models, per Table S2).

Analysis
Abbreviation
EPS-EI

GCAM-CGS

Haiku-RFF*

CCS Technologies

-Power: Fossil fuel (not
included in IRA
analysis)
-Industrial: Fossil fuel
use and processes
-Direct air capture (not
included in IRA
analysis)
-Power: CCS for new
coal, NGCC, and
biomass with different
capture assumptions
-Industrial processes
-Liquid fuel production
Power: CCS for new
coal and NGCC

IPM-NRDC*

Power: CCS retrofits
(90% and 99% capture)
for coal and NGCC,
CCS for new NGCC

MARKAL-
NETL

-Power: CCS for new
coal, NGCC, and
biomass; retrofits for
coal and NGCC
-Industrial processes
-Hydrogen production
-Direct air capture

CO2 Transport and
Storage
Not explicitly modeled,
but costs are included
in CCS costs.

H2 Production

H2 can be produced via
five different
production pathways,
including steam
methane reforming and
electrolysis.

H2 Transport and
Storage
Not modeled.

Carbon Dioxide
Removal

DAC: One
representative
technology powered by
electricity

Energy Storage
Technologies
Battery storage,
existing pumped hydro

CO2 T&S on a regional
basis with costs for
investments in pipeline
and injection capacity,
as well as ongoing
O&M costs.
EPA CO2 T&S costs
(step function for each
state). Total CO2
storage and utilization
options is scaled to 100
million short tons in
2030, doubling every
five years thereafter.
Assumptions for CO2
storage capacity/cost
from based on GeoCAT
(2021) in 37 of 48
states. CO2 transport
based on $228k/in-mi
for pipelines.
Fixed cost of CO2
transport, injection, and
long-term monitoring.
CO2 storage reservoir
capacity varies by
region.

H2 can be produced
with electrolysis.

Exogenously specified
H2 transport costs.

BECCS: Power
generation or liquid
fuel production

Battery storage,
concentrated solar
power

None

None

None

None

None

None

Battery storage (4-hr
duration), existing
pumped hydro

Battery storage (4/8/10-
hr duration), paired 4-
hr battery with solar,
existing pumped hydro
and other storage

DAC: High-
temperature with heat
from natural gas

Battery storage, H2
storage, existing
pumped hydro

H2 can be produced
with fossil resources,
biomass, or
electrolysis. Fossil and
biomass H2
technologies can be
used with CCS. Local,

Transport costs from
central H2 vary by
settlement type. Liquid
H2 can be imported by
truck or pipeline.
Distributed production
technologies combine

44

NEMS-RHG

ReEDS-
NREL*

REGEN-EPRI

RIO-REPEAT

- Power: CCS for new
coal and NGCC (Allam
cycle); retrofits for coal
and NGCC
-Industrial processes
-Hydrogen production
-Direct air capture
-Power: CCS for new
and retrofits for coal
and NGCC
-New biomass with
CCS, DAC, and H2
production modeled but
not considered in this
analysis

-Power: CCS for new
coal, NGCC, and
biomass with different
capture assumptions;
retrofits for existing
coal and NGCC
-Industrial processes
-Hydrogen production
-Direct air capture

-Power: CCS for new
NGCC and new
biomass with different
capture assumptions;
retrofits for existing
coal and NGCC;
repowering existing gas
and coal to NGCC with
CCS
-Industrial processes
-Hydrogen production

Regional CO2 T&S
costs

midsize, and central
production options.
H2 can be produced
with fossil resources or
electrolysis. Fossil can
be retrofitted with CCS.

production and
refueling capabilities.
Representation of
existing infrastructure.

DAC: Median cost
estimate among DAC
technology pathways

Battery storage,
concentrated solar
power, existing pumped
hydro

Spatially explicit cost,
investment, and
operation for CO2 T&S,
including capital and
O&M of pipeline,
injection, and storage.
Pipelines can be built
between any ReEDS
regions, as well as
between a region and a
storage reservoir.
Regional CO2 T&S
with costs for
investments in pipeline
and injection capacity,
as well as O&M costs.
Investments in inter-
regional CO2 pipeline
capacity can be made to
access capacity in
neighboring regions.

Inter-zonal CO2 T&S
through the expansion
of a CO2 transport
network, including
pipeline capital and
O&M costs, injection
costs, and spurline
costs to connect into
the trunkline system.

Available in ReEDS
but not considered in
this analysis.

Available in ReEDS
but not considered in
this analysis.

Available in ReEDS
but not considered in
this analysis.

H2 can be produced
with fossil resources,
biomass, or
electrolysis. Fossil and
biomass H2
technologies can be
used with CCS.

Endogenous
representation of H2
transport and storage
with new dedicated
infrastructure or
blending gas
commodities through
existing natural gas
infrastructure.

H2 can be produced
from natural gas (steam
methane reformation
with or without CCS,
autothermal
reformation with CCS),
biomass with CCS or
electrolysis.

Endogenous
representation of H2
transport with
dedicated infrastructure
or limited blending in
existing natural gas
infrastructure.
Endogenous hydrogen
storage technologies.

-DAC: Four
representative
technologies (high-
temperature with heat
provided by natural gas
or electricity and low-
temperature with gas
and/or electricity)
-BECCS: Power
generation or hydrogen
production
-Direct air capture
-BECCS: Power
generation, H2
production, or H2
production with
renewable fuel
production.

45

Battery storage,
pumped hydro storage
(existing and
new/uprates),
compressed air,
concentrated solar
power

Battery storage
(endogenous duration),
concentrated solar
power, compressed air,
H2 storage, existing
pumped hydro

Battery storage
(endogenous duration),
thermal energy storage,
H2 storage, existing
pumped hydro

Table S5.
Technology-specific model expansion constraints. See Table S4 for coverage of emerging technologies. Electric sector models are
designated with * (others are energy system models, per Table S2).

Analysis
Abbreviation
EPS-EI

None

Wind and Solar

Transmission

Nuclear

GCAM-CGS

Bounds on regional
resource quality

Haiku-RFF*

None

IPM-NRDC*

MARKAL-
NETL

NEMS-RHG

ReEDS-
NREL*

Short-term $/kW adder
for builds greater than
120% of annual record
builds as of 2022
through 2035
Bounds on regional
resource quality

Bounds on regional
resource quality; upper
bound of 70% regional
generation share
Bounds on regional
resource quality; lower
bounds for planned
additions through 2024

REGEN-EPRI  Bounds on regional

resource quality; lower
bounds for planned
additions (EIA-860)

None

None

None

None

Constraint on near-term
deployment and state-
level policies
Fixed to baseline levels
as a proxy for IRA
subsidies

New transmission
expansion constrained
before 2028

None

None

Economic nuclear
retirements are not
allowed through 2023
and are limited to 4
GW in 2025
None

None

CCS

None

None

Upper bound on gas
(coal) with CCS
constrained to 20 GW
(5 GW) total through
2045; upper bound on
CO2 storage of 100
million short tons in
2030, doubling every
five years thereafter
Only 6 GW of CCS
(90% capture) can be
built before 2027; 99%
capture option only
available starting 2027
Upper bound on
regional CO2 storage
reservoirs
None

Other Generation
Options

End-Use and Fuels

None

None

None

Adoption implicitly
constrained by
equipment turnover
Adoption implicitly
constrained by
equipment turnover
N/A

None

N/A

None

None

Biofuel production
constraints

Adoption implicitly
constrained by
equipment turnover

Near-term announced
additions; before 2028,
endogenous expansion
is limited to historical
maximum build rate
(1.4 TW-mi/yr)
National constraint on
total new transmission
builds in GW-miles
(10% by 2030)

None

None

None

N/A

Constraint on near-term
deployment and state-
level policies

Constraint on near-term
deployment for power;
bounds on CO2 storage

Lower bounds to reflect
under-construction
capacity (EIA-860)

Adoption implicitly
constrained by
equipment turnover

46

RIO-REPEAT  Upper bound on annual

builds, reflecting
supply chains and
interconnection,
ranging from 17-30%
annual growth rates
through 2032

Lower bounds on key
inter-regional ties to
represent the impact of
DOE loans

Constrained by state-
level policies

Geological
sequestration: Annual
limit on injection,
which relaxes as the
practice matures and
more class six wells
come online

None

For nascent
technologies, maximum
annual build constraints
to reflect maturing
markets, which relax
over time

47

Table S6.
Summary of key indicators in 2030 for IRA and reference scenarios across models. Indicators are 2030 electric sector CO2
reductions (% from 2005 levels), 2030 generation share from low-emitting technologies (%), 2030 capacity share from low-emitting
technologies (% nameplate installed capacity), 2030 coal generation decline (% from 2021 levels), economy-wide CO2 reduction (%
from 2005 levels), 2030 electric vehicle new sales share (% of new vehicle sold are battery or plug-in hybrid electric), 2030 electricity
share of final energy (%), and 2030 petroleum reduction (% from 2005 levels). Electric sector models are designated with * (others are
energy system models, per Table S2).

Metric

Ref: Electric Sector CO2
Reduction
IRA: Electric Sector CO2
Reduction
Ref: Low-Emitting
Generation Share
IRA: Low-Emitting
Generation Share
Ref: Low-Emitting
Capacity Share
IRA: Low-Emitting
Capacity Share
Ref: Unabated Coal
Generation Decline
IRA: Unabated Coal
Generation Decline
Ref: Non-Electric CO2
Reduction
IRA: Non-Electric CO2
Reduction
Ref: Electric Vehicle Sales
Share
IRA: Electric Vehicle Sales
Share
Ref: Electricity Share of
Final Energy
IRA: Electricity Share of
Final Energy

Units
% from
2005
% from
2005

%

%

%

%

% from
2021
% from
2021
% from
2005
% from
2005

%

%

%

%

EPS-EI

GCAM-
CGS

Haiku-
RFF*

IPM-
NRDC*

MARKAL
-NETL

NEMS-
RHG

ReEDS-
NREL*

REGEN-
EPRI

RIO-
REPEAT

50%

75%

51%

76%

50%

71%

52%

79%

25%

38%

29%

34%

22%

23%

47%

72%

50%

71%

48%

68%

18%

76%

25%

39%

24%

43%

23%

26%

44%

63%

56%

70%

51%

61%

3%

37%

55%

66%

46%

57%

47%

53%

60%

78%

48

41%

47%

48%

49%

52%

54%

26%

43%

31%

34%

25%

25%

60%

80%

59%

78%

53%

61%

46%

85%

30%

39%

22%

32%

24%

23%

48%

83%

54%

82%

49%

67%

23%

92%

53%

58%

55%

58%

53%

56%

26%

48%

29%

33%

32%

44%

24%

26%

59%

69%

65%

75%

58%

66%

27%

47%

29%

37%

43%

52%

23%

24%

Ref: Petroleum Decline

IRA: Petroleum Decline

% from
2005
% from
2005

25%

25%

21%

30%

11%

11%

13%

14%

31%

32%

20%

21%

49

References

1.  J. Weyant, Some Contributions of Integrated Assessment Models of Global Climate
Change. Review of Environmental Economics and Policy 11(1), 115-137 (2020).

2.  N. Hultman et al., “An All-In Climate Strategy Can Cut U.S. Emissions by 50% by
2030” (America Is All In, 2021).

3.  Joint Global Change Research Institute (JGCRI), “GCAM v5.3 Documentation, Global
Change Analysis Model (GCAM)” (2021); https://jgcri.github.io/gcam-doc/.

4.  D. Young et al., “US-REGEN Model Documentation” (3002016601, Electric Power
Research Institute, 2020); https://us-regen-docs.epri.com/v2021a/.

5.  S. Rose and M. Scott, “Grounding Decisions: A Scientific Foundation for Companies
Considering Global Climate Scenarios and Greenhouse Gas Goals” (3002014510, Electric
Power Research Institute, 2018).

6.  W. Cole et al., “Variable Renewable Energy in Long-Term Planning Models: A Multi-
Model Perspective” (NREL/TP-6A20-70528, National Renewable Energy Laboratory, 2017).

7.  J. Bistline et al., Energy Storage in Long-Term System Models: A Review of
Considerations, Best Practices, and Research Needs. Progress in Energy 2(3), 032001
(2020).

8.  M. Mahajan et al., “Modeling the Inflation Reduction Act Using the Energy Policy
Simulator” (Energy Innovation, 2022).

9.  K. Rennert et al., Comprehensive Evidence Implies a Higher Social Cost of CO2. Nature
610(7933), 687-692 (2022).

10. Congressional Budget Office, “Summary: Estimated Budgetary Effects of Public Law
117-169, to Provide for Reconciliation Pursuant to Title II of S. Con. Res. 14” (2022).

11. Credit Suisse, “U.S. Inflation Reduction Act: A Tipping Point in Climate Action” (2022).

12. J. Bistline et al., Actions for Reducing U.S. Emissions at Least 50% by 2030. Science
376(6596), 922-924 (2022).

13. U.S. Government, “A Review of Sustained Climate Action through 2020: United States
7th UNFCCC National Communication, 3rd and 4th Biennial Report” (2021).

14. U.S. Environmental Protection Agency, “Supplementary Material for the Regulatory
Impact Analysis for the Proposed Rulemaking, ‘Standards of Performance for New,
Reconstructed, and Modified Sources and Emissions Guidelines for Existing Sources: Oil
and Natural Gas Sector Climate Review’” (2022).

15. U.S. Government, “The Long-Term Strategy of the United States: Pathways to Net-Zero
Greenhouse Gas Emissions by 2050” (2021).

16. J. Bistline et al., “Nuclear Energy in Long-Term System Models: A Multi-Model
Perspective” (3002023697, Electric Power Research Institute, 2022).

17. C. Cole et al., “Policies for Electrifying the Light-Duty Vehicle Fleet in the United
States” (2023).

50

18. S. Paltsev and P. Capros, Cost Concepts for Climate Change Mitigation. Climate Change
Economics 4, 1340003 (2013).

19. J. Bistline, Metrics for Assessing the Economic Impacts of Power Sector Climate and
Clean Electricity Policies. Progress in Energy 3(4), 043001 (2021).

20. J. Bistline, The Importance of Temporal Resolution in Modeling Deep Decarbonization
of the Electric Power Sector. Environmental Research Letters 18(8), 084005 (2021).

21. C. Shearer et al., The Effect of Natural Gas Supply on US Renewable Energy and CO2
Emissions. Environmental Research Letters 9(9), 094008 (2014).

22. J. Stock and D. Stuart, “Robust Decarbonization of the US Power Sector: Policy Options”
(National Bureau of Economic Research, w28677, 2021).

51

