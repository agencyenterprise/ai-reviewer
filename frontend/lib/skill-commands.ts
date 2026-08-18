import { SKILLS } from '@/lib/generated-skills';

/**
 * Slash-command descriptions, one per skill.
 *
 * Each description is taken verbatim from the related workflow's manifest
 * (`lib/workflows/<workflow>/manifest.py` → `description`). Skills that have no
 * corresponding workflow (helper/meta skills) fall back to the skill's own
 * SKILL.md description. If a manifest description changes, update it here.
 */
const MANIFEST_DESCRIPTIONS: Record<string, string> = {
  // skill name                    // lib/workflows/<workflow>/manifest.py
  'abbreviation-scan':
    'Have you defined all abbreviations and acronyms accurately and consistently? Checks that every abbreviation is spelled out at first use and all abbreviations are listed in an Abbreviations section.', // abbreviation_scan_v2
  'about-this-authors':
    'Does the preface meet publication requirements? Checks that required elements are present: publication context, objectives, audience, funding, author bios.', // about_this_ger
  'about-this-preface':
    'Does the preface meet publication requirements? Checks that required elements are present: publication context, objectives, audience, funding, author bios.', // about_this_ger
  'advocacy-tone':
    'Does your document use neutral, objective language? Flags advocacy language, trigger words, and subjective tone using fast pattern matching (regex) followed by LLM verification.', // advocacy_tone
  'citation-support':
    'Do your citations actually back up what you claim they say? Cross-checks claims against the full text of your reference PDFs. Provide your reference documents before running.', // claim_reference_validation
  'document-contents':
    'Does your document include all required content? Checks that key content is present: About This, Acknowledgements, Methods, Results, Conclusion, References, and Appendix (when referenced in the text).', // document_structure
  'figures-tables-check':
    'Are all figures and tables properly titled, numbered, and referenced? Checks that every figure and table has a title, is consistently numbered, is cited in the body text, and that all body-text references resolve to an actual figure or table.', // figures_tables_check
  'inference-validation':
    "Does your reasoning hold up? Flags logical leaps, unsupported conclusions, and arguments where the evidence doesn't support the claim.", // inference_validation_v2
  'methodology-comparison':
    'Does your methodology match standard practices in the literature? Uses web search to find standard methods for a topic area, then compares them against your approach.', // methodological_alignment
  'recommendation-check':
    "Are the document's recommendations supported by its own findings? Flags recommendations that lack backing evidence in the body, or where the evidence is weak, indirect, or contradictory.", // recommendation_check
  'reference-download':
    'Search the web for each reference and download the related full text when available (PDF or Markdown).', // reference_downloader
  'reference-extraction':
    'Extract bibliographic references from the document using section detection and windowed extraction.', // reference_extraction
  'reference-validation':
    'Are your references accurate? Uses web search to check each citation exists online and that the author, title, publisher, and year match public sources. Useful for catching typos or hallucinated references.', // reference_validation_v2
  'reproducibility-check':
    'Could someone reproduce your results from the document alone? Extracts main results and classifies each by how reproducible it is based on whether the data is present and the methodology is described.', // results_extraction
  'reviewer-2':
    "Simulates a full peer review, returning a structured critique with strengths, weaknesses, actionable next steps, and a devil's-advocate rebuttal.", // reviewer_2
};

export interface SkillCommand {
  /** Skill name — used as the slash-command id / trigger. */
  id: string;
  /** Description shown in the slash-command menu (from the workflow manifest). */
  description: string;
}

// One slash command per skill, kept in sync with the generated skill list.
export const SKILL_COMMANDS: SkillCommand[] = SKILLS.map((skill) => ({
  id: skill.name,
  description: MANIFEST_DESCRIPTIONS[skill.name] ?? skill.description,
}));
