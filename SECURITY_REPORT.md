# Portfolio Security Report

Review date: 31 July 2026

## Scope

Reviewed the complete current GitHub Pages repository, including all HTML,
CSS, JavaScript, repository paths and Git history. The downloadable résumé
PDF was checked for embedded metadata, local paths, credentials and unexpected
URLs. Public external links were tested over HTTPS.

## 1. Security issues found

- External links that opened a new tab used `rel="noopener"` but omitted
  `noreferrer`.
- The space-and-range simulator used an inline `onsubmit` handler.
- Demo rendering code uses `innerHTML` for charts and tables. Its inputs are
  hard-coded synthetic data and constrained numeric form values; no remote or
  user-authored HTML enters these renderers, so no exploitable injection path
  was identified in the current static site.
- The résumé contains ordinary generator metadata (`Writer`/`LibreOffice`) and
  intentional public GitHub and LinkedIn URLs. No private file path, credential
  or confidential metadata was found.

No API keys, access tokens, passwords, database credentials, private
certificates, SSH keys, service-account keys, environment variables, private
endpoints, localhost references, internal company paths, source maps, debug
logs, backup files or temporary files were found in the current repository or
its reachable Git history.

## 2. Security improvements implemented

- Added `rel="noopener noreferrer"` to every external link that uses
  `target="_blank"`.
- Replaced the inline submit handler with an external JavaScript event listener.
- Added descriptive accessible labels to project actions and marked decorative
  arrow glyphs as hidden from assistive technology.
- Preserved HTTPS for every external resource and link.
- Kept the site free of third-party scripts. The only third-party resource is
  the existing Google Fonts stylesheet.

## 3. Remaining recommendations

- Keep all future demo-renderer inputs local and typed. If remote or
  user-authored data is introduced later, replace template-based `innerHTML`
  rendering with DOM construction and `textContent`, or apply strict
  sanitisation.
- Consider self-hosting the existing fonts if removing the final third-party
  request becomes a privacy requirement.
- Repeat secret and metadata scans whenever new documents or downloadable
  datasets are added.
- Enable GitHub secret scanning and Dependabot alerts where available, even
  though the current site has no package dependencies.

## 4. Overall security rating

**Low risk.**

The deployment contains static HTML, CSS, JavaScript and one PDF only. There is
no server-side code, executable backend, upload function, authentication flow
or database connection in this repository. The public demos use local or
synthetic data and do not expose production credentials.

## Link verification

The homepage, Product Sales Growth Treemap, InvTracker demo, InvTracker GitHub
repository, both Streamlit projects, GitHub profile and Google Fonts stylesheet
returned HTTP 200 on 31 July 2026. LinkedIn returned its automated-request
blocking status 999; the public HTTPS profile URL was retained because this is
an expected bot-protection response rather than evidence of a broken redirect.
