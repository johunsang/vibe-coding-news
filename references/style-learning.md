# Learning the user's writing style

Use this when the user wants post drafts in their own voice and has no style guide yet.

## 1. Get their posts (only theirs, only with their consent)

Best to worst:
1. They paste or export posts (Threads/X/LinkedIn data export, a text file, a blog feed).
2. Their public profile opened in a browser tool where **they are already signed in**. Scroll and collect only posts authored by them. Never sign in for them, never read DMs.
3. A public RSS/Atom feed of their blog.

Aim for 100+ posts. Save the raw text locally (for example `<output_dir>/style/posts.json`) and keep it out of anything you publish.

## 2. Measure, then describe

Compute from the posts:
- Median and average length, lines per post, how often they break lines
- Punctuation habits (periods or none, ellipses, exclamation marks)
- Emoji and hashtag frequency
- Formal vs casual endings, laughter or slang tokens, recurring catchphrases
- How links appear (end of post, separate reply, none)
- Typical moves: numbers as evidence, a closing joke, self-deprecation, lists

## 3. Write the guide

Save `<output_dir>/style/style-guide.md` with:
- **Identity**: how they present themselves (role, years, what they build)
- **Format**: length, line breaks, lists, link placement
- **Voice**: register, signature words, what they never do
- **Content patterns**: 3–5 recurring moves with short paraphrased examples (not verbatim copies)
- **Avoid**: tones that would sound unlike them

Point `style_guide` in `config.json` at this file. Re-run when their voice drifts, or every few months.
