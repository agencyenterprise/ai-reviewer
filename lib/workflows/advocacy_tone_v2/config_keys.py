"""Runtime config key for the Advocacy & Tone (v2) workflow.

A single admin-overridable text setting (looked up via the AppConfig table)
holds the deployment-tunable configuration for the advocacy/tone review: the
trigger words, advocacy phrases, sections to skip, and what each issue type
means. The `advocacy-tone` skill remains the portable *method*; this setting is
the deployment's *data*, injected into the prompt at runtime and superseding the
skill's built-in defaults.

The default below mirrors the skill's built-in defaults, so out-of-the-box
behavior matches the skill. Admins edit this one text field in the app-config UI.
"""

from lib.services.app_configs import DefaultConfig

ADVOCACY_TONE_V2_CONFIG_KEY = "advocacy_tone_v2.config"

_DEFAULT_CONFIG = """\
Trigger words (certainty language without evidence):
obviously, clearly, undoubtedly, certainly, definitely, absolutely, always, never

Advocacy phrases (unsupported recommendations):
we believe, in our opinion, it is clear that, without doubt, everyone knows

Skip sections whose heading contains:
author, reference, bibliography, appendix, acknowledgment

What each issue type means:
- Trigger words — certainty language without evidence. Words implying certainty or universal truth without supporting evidence; academic writing should hedge claims appropriately.
- Advocacy language — unsupported recommendations. Statements promoting positions without citing evidence; research should distinguish between findings and opinions.
- Subjective tone — subjective evaluations. Value judgments or emotional language that may indicate bias; research writing should maintain a neutral, evidence-based tone.
"""

ADVOCACY_TONE_V2_DEFAULTS = [
    DefaultConfig(
        key=ADVOCACY_TONE_V2_CONFIG_KEY,
        default_value=_DEFAULT_CONFIG,
        description=(
            "Deployment configuration for the Advocacy & Tone (v2) workflow. "
            "Plain text, edited here in the UI: the trigger words, advocacy "
            "phrases, sections to skip, and the definition of each issue type. "
            "It is injected into the review prompt and supersedes the skill's "
            "built-in defaults — so you can tune what the check looks for "
            "without changing code or the skill."
        ),
    ),
]
