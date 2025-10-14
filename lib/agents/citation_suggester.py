from enum import Enum
import asyncio
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from lib.models.agent import Agent


class ReferenceType(str, Enum):
    WEBPAGE = "WEBPAGE"
    BOOK = "BOOK"
    ARTICLE = "ARTICLE"
    OTHER = "OTHER"


class RecommendedAction(str, Enum):
    ADD_NEW_CITATION = "ADD_NEW_CITATION"
    CITE_EXISTING_REFERENCE_IN_NEW_PLACE = "CITE_EXISTING_REFERENCE_IN_NEW_PLACE"
    REPLACE_EXISTING_REFERENCE = "REPLACE_EXISTING_REFERENCE"
    DISCUSS_REFERENCE = "DISCUSS_REFERENCE"
    NO_ACTION = "NO_ACTION"
    OTHER = "OTHER"


class PublicationQuality(str, Enum):  # TODO: play with these options
    HIGH_IMPACT_PUBLICATION = "HIGH_IMPACT_PUBLICATION"
    MEDIUM_IMPACT_PUBLICATION = "MEDIUM_IMPACT_PUBLICATION"
    LOW_IMPACT_PUBLICATION = "LOW_IMPACT_PUBLICATION"
    NOT_A_PUBLICATION = "NOT_A_PUBLICATION"


class ConfidenceInRecommendation(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Reference(BaseModel):
    title: str = Field(
        description="Canonical title for the reference exactly as it should appear in the article's bibliography"
    )
    type: ReferenceType = Field(
        description="Format classification for the reference (webpage, book, article, or other)"
    )
    link: str = Field(
        description="Stable URL or DOI that lets the author retrieve the reference quickly"
    )
    bibliography_info: str = Field(
        description="Bibliography entry formatted in the article's style; reuse the existing entry when the source is already in the bibliography"
    )
    is_already_cited_elsewhere: bool = Field(
        description="A boolean value indicating whether the reference is already cited elsewhere in the document"
    )
    index_of_associated_existing_reference: int = Field(
        description="The index of the existing reference that this citation refers to, if any. Indices start at 1. If the citation does not refer to an existing reference in the bibliography, this should be -1."
    )
    publication_quality: PublicationQuality = Field(
        description="The quality of the publication that carries the suggested reference"
    )
    related_excerpt: str = Field(
        description="Exact sentence or excerpt from the our document that should cite or discuss this reference"
    )
    related_excerpt_from_reference: str = Field(
        description="Exact sentence or excerpt from the reference that is why we should cite or discuss it"
    )
    rationale: str = Field(
        description="Brief explanation of why the reference strengthens, updates, or contextualizes the focused paragraph"
    )
    recommended_action: RecommendedAction = Field(
        description=(
            "Action to take for this reference: add_citation, replace_existing_reference, "
            "discuss_reference, no_action, or other"
        )
    )
    explanation_for_recommended_action: str = Field(
        description="Specific guidance for applying the recommended action, including citation placement or text revisions"
    )
    confidence_in_recommendation: ConfidenceInRecommendation = Field(
        description="The confidence in the recommendation"
    )


class CitationSuggestionResponse(BaseModel):
    relevant_references: list[Reference] = Field(
        description="Ordered list of the most relevant references the author should consider when revising the paragraph"
    )
    rationale: str = Field(
        description="High-level reasoning summarizing how the recommendations improve the paragraph's literature coverage"
    )


class CitationSuggestionResultWithClaimIndex(CitationSuggestionResponse):
    chunk_index: int
    claim_index: int


_citation_suggester_agent_prompt = ChatPromptTemplate.from_template(
    """
# Role
You are an expert literature review researcher tasked with ensuring a paragraph cites the strongest and most current sources available while adhering to RAND Corporation's strict attribution guidelines.

# Goal
Given the full article, its extracted bibliography, and a paragraph to revise, identify references that should be cited or discussed to improve that paragraph's attribution compliance. These may be:
- Existing references already listed in the bibliography but not cited in this paragraph.
- New, high-quality sources found via web research that support claims requiring attribution.

# RAND Attribution Requirements
You must ensure the paragraph follows RAND's Three Rules of Attribution:

1. **Ideas, Opinions, Theories, Facts, Arguments, Statistics**: If the paragraph uses any idea, opinion, theory, fact, argument, or statistic from a source, it MUST cite that source.

2. **Exact Words**: If the paragraph uses exact words from a source, it MUST cite that source and use quotation marks (or block quotes).

3. **Accurate Connection**: If a source is cited, it must be connected to the work accurately, ensuring the use remains faithful to the original author's intent.

# Instructions
1. Read the paragraph in the context of the full document and bibliography to understand the existing argument and cited sources.
2. Identify ALL instances where attribution is required but missing:
   - Unsourced facts, data, or technical details that are not common knowledge
   - Statistics, percentages, or numerical claims without citations
   - Specific claims about policies, procedures, or historical events
   - Technical descriptions or methodologies
   - Arguments or interpretations that appear to be from other sources
3. Reuse relevant bibliography entries whenever they meaningfully support the paragraph but are currently uncited. Quote the entry exactly in `bibliography_info` and include a stable link.
4. Perform focused web research for key claims, statistics, or notable concepts that lack adequate support. Prefer authoritative sources (peer-reviewed articles, reputable institutions) and capture publication details for `bibliography_info`.
5. For every recommended reference:
   - Use `related_excerpt` to quote the precise sentence(s) that should cite or discuss the source.
   - Select `recommended_action` from {{"add_citation", "replace_existing_reference", "discuss_reference", "no_action", "other"}}.
   - In `explanation_for_recommended_action`, describe exactly where to place the citation or how to revise the text (e.g., "Add citation after the sentence describing X" or "Replace the existing citation to Y with this systematic review because …").
   - Specify what type of attribution is needed (fact, statistic, exact quote, idea, etc.)
6. Provide only high-impact recommendations (typically 1-5). Avoid duplicates and clearly distinguish whether the source comes from the existing bibliography or is newly discovered.
7. Summarize your overall reasoning in the response `rationale`, focusing on attribution compliance.
8. Do not fabricate references. If confident support cannot be found, omit the recommendation.

# Source Quality Standards
- Prefer peer-reviewed academic sources, government publications, and reputable institutions
- Avoid Wikipedia and other tertiary sources unless the research specifically focuses on user-generated content
- Verify that sources are current and authoritative
- Ensure sources are accessible to readers (provide stable URLs or DOIs when possible)
- For web sources, include access dates and stable URLs

## The full document that the chunk is a part of
```
{full_document}
```

## The list of bibliography entries (if any) extracted from the bibliography section of the full document
The indexes in this list should be used when returning index_of_associated_bibliography.
```
{bibliography}
```

## The paragraph of the original document that contains the chunk of text that we want to analyze
```
{paragraph}
```

## The chunk of text suggest citations for (if appropriate)
```
{chunk}
```

## The claim that is inferred from the chunk of text to be supported with additional references if appropriate
{claim}

## The list of references currently cited to support the claim and their associated supporting document (if any)
{cited_references}

## A literature review report created by the literature review agent
Consider this literature review report, but only take its recommendations into account if you think they are highly relevant to the claim, chunk, and paragraph.
It is ok if you do not recommend any references from the literature review report.
It is ok to double check anything you add by doing web searches.
```
{literature_review_report}
```
"""
)

citation_suggester_agent = Agent(
    name="Citation Suggester",
    description="Review a chunk of text against RAND attribution guidelines to identify missing citations and recommend high-quality sources for proper attribution compliance",
    model="openai:gpt-5",
    use_responses_api=True,
    use_react_agent=False,
    use_direct_llm_client=True,  # To use open ai tools (openai_web_search, openai_code_interpreter)
    use_background_mode=False,
    prompt=_citation_suggester_agent_prompt,
    tools=["openai_web_search"],
    mandatory_tools=[],
    output_schema=CitationSuggestionResponse,
)


if __name__ == "__main__":
    response = asyncio.run(
        citation_suggester_agent.apply(
            {
                "full_document": """# Some statistics about the office of the US president
Over the course of the US history, the office of the US president has changed hand dozens of times. Various types of exchanges has happened, ranging from the same president being elected more than twice (i.e., Franklin D. Roosevelt) to the president being removed from office (i.e., Andrew Johnson).

One thing that has never happened, is that a one-term president comes back to office in a later term after losing one reelection bid. So surely, based on this track record alone it seems exceedingly unlikely that former president Trump would be able to defeat President Joe Biden in the 2024 election.
""",
                "bibliography": """Foner, E. (2014). Reconstruction: America's Unfinished Revolution, 1863-1877. New York, NY: Harper & Row.
Skowronek, S. (2011). Presidential Leadership in Political Time. Lawrence, KS: University Press of Kansas.
""",
                "paragraph": """One thing that has never happened, is that a one-term president comes back to office in a later term after losing one reelection bid. So surely, based on this track record alone it seems exceedingly unlikely that former president Trump would be able to defeat President Joe Biden in the 2024 election.""",
                "chunk": """One thing that has never happened, is that a one-term president comes back to office in a later term after losing one reelection bid. So surely, based on this track record alone it seems exceedingly unlikely that former president Trump would be able to defeat President Joe Biden in the 2024 election.""",
                "claim": """So surely, based on this track record alone it seems exceedingly unlikely that former president Trump would be able to defeat President Joe Biden in the 2024 election.""",
                "cited_references": """""",
                "literature_review_report": """Below is a structured, topic-by-topic briefing you can use to improve the article. For each topic, I list what’s currently in the text, what’s inaccurate or under-supported, and high-quality sources you can cite. I also indicate how these sources could be integrated into the article.

Executive snapshot
- Main issues to fix or qualify:
  - A number of factual inaccuracies about impeachment and removal (Andrew Johnson was impeached but not removed).
  - A concrete counterexample to the claim that “a one-term president never returns after losing reelection” (Grover Cleveland served two nonconsecutive terms).
  - The article’s projection about the 2024 election should be grounded in actual results and credible analysis.
  - The article could benefit from situating its claims within established political-time/theory literatures (Skowronek) and reconstructive history (Foner) to avoid overly simplistic historical generalizations.
- Strong, current sources exist to correct or nuance these points (see topic-by-topic below).

Topic 1. The claim that Andrew Johnson was “removed from office” (impeachment vs removal)
What’s in the article
- “the president being removed from office (i.e., Andrew Johnson)” implies Johnson was removed from office through impeachment.

What’s wrong or under-supported
- Andrew Johnson was impeached by the House but was acquitted by the Senate and thus not removed from office. This is a classic historical point that is routinely misunderstood.

Recommended high-quality sources to cite
- Britannica: Andrew Johnson – The presidency (impeachment section; explicit note that Johnson was impeached but not removed). ([britannica.com](https://www.britannica.com/biography/Andrew-Johnson?utm_source=openai))
- U.S. Senate: Impeachment Trial of Andrew Johnson (official pages detailing the trial and the acquittal by the Senate). ([senate.gov](https://www.senate.gov/about/powers-procedures/impeachment/impeachment-johnsonandrew.htm?utm_source=openai))
- National Archives: Impeachment (historical overview and the Johnson impeachment’s fate). ([archives.gov](https://www.archives.gov/legislative/features/impeachment?utm_source=openai))
- History.com (for accessible summary of the Johnson impeachment and a comparison to later impeachments). ([history.com](https://www.history.com/this-day-in-history/president-andrew-johnson-impeached?utm_source=openai))

How to fit this in the document
- Replace or revise the phrasing “the president being removed from office (i.e., Andrew Johnson)” with a sentence that clarifies:
  - Johnson was impeached by the House in 1868 but was not removed after the Senate trial (acquitted by one vote). Then briefly note that impeachment is a political process, not automatic removal. Use the Britannica and Senate/NARA sources to anchor this correction. ([britannica.com](https://www.britannica.com/biography/Andrew-Johnson?utm_source=openai))

Topic 2. Grover Cleveland as a counterexample to “one-term presidents never return”
What’s in the article
- The piece implies a one-term president has never returned to win office in a later term after losing reelection.

What’s wrong or under-supported
- Grover Cleveland is the famous counterexample: he served as the 22nd president (1885–1889), lost the 1888 election, and then won again as the 24th president (1893–1897), making him the only president to serve two nonconsecutive terms.

Recommended high-quality sources to cite
- Britannica: Grover Cleveland – biography and the fact he served nonconsecutive terms (22nd and 24th). ([britannica.com](https://www.britannica.com/biography/Grover-Cleveland?utm_source=openai))
- Britannica: Grover Cleveland (overview) – reinforcing the “nonconsecutive terms” point. ([britannica.com](https://www.britannica.com/biography/Grover-Cleveland?utm_source=openai))
- History.com or NPR summaries (for accessible narrative of his two terms). See History.com’s Grover Cleveland article. ([history.com](https://www.history.com/articles/grover-cleveland?utm_source=openai))
- AP coverage (for contemporary framing that Trump’s situation in 2024 has publicized Cleveland’s precedent). ([apnews.com](https://apnews.com/article/7ea2c92c72911462ccb1bc2e7352fa23?utm_source=openai))

How to fit this in the document
- After the sentence about the “never comes back” claim, insert a brief corrective note: “Grover Cleveland is the sole counterexample of a president who served two nonconsecutive terms; he was the 22nd and 24th president (1885–1889 and 1893–1897).” Cite Britannica (turn0search0 or turn3search2) for the factual claim, and optionally include a secondary note with History.com or NPR for public-facing context (turn3search5). ([britannica.com](https://www.britannica.com/biography/Grover-Cleveland?utm_source=openai))

Topic 3. The historical record of presidential transitions (the “dozens of changes” claim)
What’s in the article
- The opening line suggests “the office of the US president has changed hand dozens of times.”

What’s right or plausible
- There have been many transitions, and exact counts depend on whether you count nonconsecutive terms as separate presidencies.

Recommended high-quality sources to cite
- Britannica: List of presidents of the United States (gives the count of presidencies and notes the nonconsecutive-term issue). ([britannica.com](https://www.britannica.com/topic/Presidents-of-the-United-States-1846696?utm_source=openai))
- Britannica: Presidents of the United States (general page) and the “list of presidents” section for context on the term-length, succession, and counting conventions. ([britannica.com](https://www.britannica.com/topic/presidents-of-the-United-States-2226856?utm_source=openai))

How to fit this in the document
- Consider revising the opening sentence to a specific, sourced figure, e.g.: “There have been 47 presidencies shared by 45 individuals (due to Grover Cleveland’s nonconsecutive terms).” Then attach the Britannica source after that sentence. This provides precision and credible grounding. ([britannica.com](https://www.britannica.com/topic/Presidents-of-the-United-States-1846696?utm_source=openai))

Topic 4. The 22nd Amendment (term limits) and the possibility of a third term
What’s in the article
- The article treats term limits as a barrier that would make a third nonconsecutive term unlikely for Trump.

What’s right or plausible
- The 22nd Amendment restricts presidents to two elected terms; this is a foundational constitutional constraint. There’s ongoing public discussion about potential changes, but formal repeal or replacement would require a constitutional amendment.

Recommended high-quality sources to cite
- Britannica: Twenty-second Amendment (term limits) – clear description of term limits and the historical rationale. ([britannica.com](https://www.britannica.com/topic/Twenty-second-Amendment?utm_source=openai))
- Reagan Library: Official text and background on the 22nd Amendment. ([reaganlibrary.gov](https://www.reaganlibrary.gov/constitutional-amendments-amendment-22-term-limits-presidency?utm_source=openai))
- Reuters fact-check: Clarifies the constitutional status of the 22nd Amendment and its ratification history. ([reuters.com](https://www.reuters.com/fact-check/congress-did-not-violate-constitution-by-passing-22nd-amendment-2024-07-16/?utm_source=openai))
- Britannica: List of presidents (context that the two-term limit has shaped modern presidencies). ([britannica.com](https://www.britannica.com/topic/Presidents-of-the-United-States-1846696?utm_source=openai))

How to fit this in the document
- Add a short paragraph noting that the 22nd Amendment restricts elected terms to two; mention that there is public discussion about revising or circumventing it, but emphasize that current law adheres to a two-term limit. Support with Britannica turn4search3 and Reagan Library turn5search1; and for contemporary debates or misunderstandings, the Reuters fact-check (turn5news12) provides a neutral legal framing. ([britannica.com](https://www.britannica.com/topic/Twenty-second-Amendment?utm_source=openai))

Topic 5. The 2024 U.S. presidential election results and what they imply for the article’s argument
What’s in the article
- The piece posits that it would be “exceedingly unlikely” for Trump to win in 2024, based on past patterns.

What’s right or plausible
- In reality, the 2024 election concluded with Donald Trump winning the presidency, reversing 2020 results in which he lost to Biden. Grounding this claim in actual results is essential.

Recommended high-quality sources to cite
- AP News: Trump elected president in 2024 and later certification (January 2025) – credible reporting on the result and the certification process. ([apnews.com](https://apnews.com/article/83c8e246ab97f5b97be45cdc156af4e2?utm_source=openai))
- AP News: Congress certifies Trump’s 2024 win (January 6, 2025) – official certification details. ([apnews.com](https://apnews.com/article/b8284b9b6b22f78ab7f23f8c8b3c3da3?utm_source=openai))
- BBC: Harris certifies Trump’s win (January 6, 2025) – independent international coverage confirming the outcome and the certification process. ([bbc.com](https://www.bbc.com/news/articles/cd9x33z8nzpo?utm_source=openai))
- CNBC/Bloomberg/Reuters coverage (as supplemental, non-Wikipedia sources) confirming the certified result and the political context. ([cnbc.com](https://www.cnbc.com/2025/01/06/congress-trump-harris-election-certification-jan-6.html?utm_source=openai))

How to fit this in the document
- Replace the sentence that frames Trump’s defeat as “exceedingly unlikely” with a concise ±contextual note: “In the 2024 election, Donald Trump defeated Kamala Harris and won the presidency; Congress certified the result on January 6, 2025” and provide sources. This corrects the article’s factual trajectory and aligns with credible reporting. ([apnews.com](https://apnews.com/article/83c8e246ab97f5b97be45cdc156af4e2?utm_source=openai))

Topic 6. Theoretical framing: Skowronek’s presidential leadership in political time and Foner’s Reconstruction
What’s in the bibliography now
- Foner (2014). Reconstruction: America's Unfinished Revolution, 1863–1877.
- Skowronek (2011). Presidential Leadership in Political Time.

What’s missing or could be strengthened
- The article would benefit from clearly signaling how these works illuminate patterns of presidential power, legitimacy, and transitions—especially when discussing nonconsecutive terms, impeachments, or dramatic political realignments.

Recommended high-quality sources to cite (to connect theory to the article)
- Skowronek, Presidential Leadership in Political Time (2008 edition; reprise and reappraisal). The Yale department page (turn6search3) and Cambridge/academic reviews (turn6search8) provide accessible summaries and critical receptions.
- Yale ISPS blog summarizing Skowronek’s application to contemporary elections (turn6search7) can help bridge theory with Trump-era politics.
- History News Network piece contextualizing Skowronek’s “political time” in relation to Trump’s rise (turn6search9). These sources help the reader see how “regime politics” may shape unusual electoral outcomes, including nonconsecutive terms.
- Foner’s Reconstruction (Updated Edition, 2014) as a foundational model of long-run political change and coalition-building in American history (publisher/edition details in turn10search1 and turn10search0).

How to fit this in the document
- Add a short “theoretical framing” paragraph or footnotes:
  - Use Skowronek to frame how presidents are situationally situated within competing coalitions and how “regime” shifts can enable or constrain ambitious returns (e.g., nonconsecutive terms). Cite Skowronek (turn6search3) and the Yale page (turn6search3) or Cambridge core review (turn6search8).
  - Use Foner to situate Reconstruction as a long-run pressure-test on legitimacy and constitutional arrangements, which can contextualize debates about term limits and impeachment (cite Foner’s updated edition details, turn10search1).
  - Provide a caution that Skowronek’s theory emphasizes historical patterns but does not predict individual outcomes with certainty; cite the Cambridge review (turn6search8) for a critical perspective. ([politicalscience.yale.edu](https://politicalscience.yale.edu/publications/presidential-leadership-political-time-reprise-and-reappraisal-third-edition?utm_source=openai))

Topic 7. The factual scaffolding around “dozens of handoffs” and the terminology of terms
What to fix or clarify
- Rather than a vague “dozens of handoffs,” provide a precise, sourced metric of transitions and terms, including how nonconsecutive terms are counted in the presidency.

Recommended high-quality sources to cite
- Britannica: List of presidents (with explicit note on counting conventions and nonconsecutive terms). ([britannica.com](https://www.britannica.com/topic/Presidents-of-the-United-States-1846696?utm_source=openai))
- Britannica: Twenty-second Amendment (for term-limit context). ([britannica.com](https://www.britannica.com/topic/Twenty-second-Amendment?utm_source=openai))

How to fit this in the document
- Replace the vague language with a precise sentence such as: “Since 1789 there have been 47 presidencies across 45 individuals, due to Grover Cleveland’s nonconsecutive terms.” Attach the Britannica sources after that sentence. ([britannica.com](https://www.britannica.com/topic/Presidents-of-the-United-States-1846696?utm_source=openai))

Topic 8. Reconstruction and the current argument’s broader narrative
What to add
- The article’s opening could be strengthened by incorporating a concise note about the scale and stakes of Reconstruction-era reforms and constitutional changes, connected to how we think about modern executive power.

Recommended high-quality sources to cite
- Foner (Reconstruction) for the scope and stakes of Reconstruction and for how constitutional structures and civil rights evolved in that era. Publisher/edition details in turn10search1.
- Cambridge/Review references to provide scholarly context on the era’s political economy and constitutional arrangements (turn11search0; turn11search0; turn6search0).

How to fit this in the document
- Add a sentence linking the broad structural shifts of Reconstruction to current debates about presidential power and constitutional rules, with a citation to Foner (updated edition) and a nod to Skowronek’s framing of regime change (turn10search1; turn6search3). ([barnesandnoble.com](https://www.barnesandnoble.com/w/reconstruction-updated-edition-eric-foner/1129142102?utm_source=openai))

Structured recommendations for bibliography edits
- Preserve core, high-quality items already in the bibliography (Foner 2014; Skowronek 2011) but augment with precise, citable corrections:
  - Add: Britannica. Grover Cleveland (two-term nonconsecutive) – to ground the Cleveland example. ([britannica.com](https://www.britannica.com/biography/Grover-Cleveland?utm_source=openai))
  - Add: Britannica. List of Presidents of the United States (context on term counts and nonconsecutive terms). ([britannica.com](https://www.britannica.com/topic/Presidents-of-the-United-States-1846696?utm_source=openai))
  - Add: Britannica. Twenty-second Amendment (term limits). ([britannica.com](https://www.britannica.com/topic/Twenty-second-Amendment?utm_source=openai))
  - Add: Britannica. Andrew Johnson (impeached but not removed) – to support impeachment correction. ([britannica.com](https://www.britannica.com/biography/Andrew-Johnson?utm_source=openai))
  - Add: U.S. Senate. Impeachment Trial of Andrew Johnson (official trial record). ([senate.gov](https://www.senate.gov/about/powers-procedures/impeachment/impeachment-johnsonandrew.htm?utm_source=openai))
  - Add: National Archives. Impeachment (official history context). ([archives.gov](https://www.archives.gov/legislative/features/impeachment?utm_source=openai))
  - Add: AP News. Trump elected president in 2024 and subsequent certification (to support the actual outcome). ([apnews.com](https://apnews.com/article/83c8e246ab97f5b97be45cdc156af4e2?utm_source=openai))
  - Add: AP News. Congress certifies Trump’s 2024 win (Jan 6, 2025). ([apnews.com](https://apnews.com/article/b8284b9b6b22f78ab7f23f8c8b3c3da3?utm_source=openai))
  - Add: BBC/other credible outlets confirming certification (to triangulate the result). ([bbc.com](https://www.bbc.com/news/articles/cd9x33z8nzpo?utm_source=openai))
  - Add: Yale/Bridges to Skowronek (summaries of his theory for accessibility in the text). ([politicalscience.yale.edu](https://politicalscience.yale.edu/publications/presidential-leadership-political-time-reprise-and-reappraisal-third-edition?utm_source=openai))
  - Add: Foner’s Reconstruction updated edition page (publisher info) to ground the discussion in credible scholarship. ([barnesandnoble.com](https://www.barnesandnoble.com/w/reconstruction-updated-edition-eric-foner/1129142102?utm_source=openai))

Notes on dates and context
- If the article discusses “the 2024 election,” anchor statements with absolute dates:
  - Election date: November 5, 2024.
  - Certification date (Congress vote): January 6, 2025. This is when credible outlets reported the formal certification, and you should cite primary/credible outlets for these dates (AP News turn8news12; BBC turn8search2; CNBC turn8search4; Bloomberg turn8search6). ([apnews.com](https://apnews.com/article/b8284b9b6b22f78ab7f23f8c8b3c3da3?utm_source=openai))

Concise editing plan (how to implement)
- Step 1: Correct factual inaccuracies
  - Replace Johnson-impeached-but-removed phrasing with Johnson-impeached-but-not-removed; add citations (Britannica turn9search8; Senate turn9search5; National Archives turn9search4). ([britannica.com](https://www.britannica.com/biography/Andrew-Johnson?utm_source=openai))
  - Introduce Grover Cleveland as a counterexample to the “one-term comeback” claim; add Britannica turn0search0 or turn3search2 (and optionally NPR/History.com for accessible narrative). ([britannica.com](https://www.britannica.com/biography/Grover-Cleveland?utm_source=openai))
- Step 2: Ground the “dozens of changes” claim
  - Add a precise figure and cite Britannica’s presidency list (turn4search2) after a sentence like: “There have been 47 presidencies across 45 individuals (as of 2025), including one nonconsecutive-term case.” ([britannica.com](https://www.britannica.com/topic/Presidents-of-the-United-States-1846696?utm_source=openai))
- Step 3: Update the 2024 election discussion
  - State the actual outcome: Trump won the 2024 election; Congress certified the result on January 6, 2025; cite AP News turn1news14 and turn8news12, and BBC turn8search2 as corroboration. ([apnews.com](https://apnews.com/article/83c8e246ab97f5b97be45cdc156af4e2?utm_source=openai))
- Step 4: Introduce theory to frame the narrative
  - Add a short paragraph linking the piece to Skowronek’s “political time” framework and Foner’s Reconstruction narrative; cite Yale/turn6search3 and Cambridge/turn6search8 for scholarly framing, and Foner turn10search1 for historical breadth. ([politicalscience.yale.edu](https://politicalscience.yale.edu/publications/presidential-leadership-political-time-reprise-and-reappraisal-third-edition?utm_source=openai))

Would you like me to draft a revised, citation-annotated version of the opening paragraph and the problematic sentences now, using these sources? I can deliver a compact revision that preserves your voice while correcting the factual points and embedding the new references.""",
            }
        )
    )
    print(response)
