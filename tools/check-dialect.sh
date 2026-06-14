#!/usr/bin/env sh
# check-dialect.sh - flag American spellings in project-authored Markdown.
#
# House dialect is British English, Oxford spelling: -ize for the Greek suffix
# (organize, authorize) with the British -our/-re/-ce forms kept (behaviour,
# centre, licence). This check guards only the classes we keep British. It does
# NOT police -ize vs -ise, because Oxford spelling uses -ize. Adopted standards
# (CODE_OF_CONDUCT.md, an upstream Contributor Covenant) are exempt by design.
#
# Usage: tools/check-dialect.sh [file ...]    (defaults to tracked *.md)
set -u

# American:British. -ize forms are deliberately absent. The list is conservative
# to avoid false positives (e.g. "meter" the device, "license" the verb, and
# "program"/"disk", which are standard in British technical usage, are omitted).
PAIRS='behavior:behaviour behaviors:behaviours color:colour colors:colours
colored:coloured coloring:colouring neighbor:neighbour neighbors:neighbours
favor:favour favored:favoured honor:honour honored:honoured labor:labour
flavor:flavour rigor:rigour harbor:harbour armor:armour vapor:vapour
center:centre centers:centres centered:centred fiber:fibre fibers:fibres
theater:theatre defense:defence offense:offence analyze:analyse
analyzed:analysed analyzes:analyses analyzing:analysing paralyze:paralyse
catalog:catalogue dialog:dialogue analog:analogue gray:grey
modeling:modelling modeled:modelled labeled:labelled labeling:labelling
signaling:signalling canceled:cancelled canceling:cancelling
traveled:travelled traveling:travelling aluminum:aluminium
enroll:enrol enrollment:enrolment fulfill:fulfil'

if [ "$#" -gt 0 ]; then
  FILES="$*"
else
  FILES=$(git ls-files '*.md' ':!:CODE_OF_CONDUCT.md')
fi

[ -n "$FILES" ] || { echo "no Markdown files to check"; exit 0; }

found=0
for pair in $PAIRS; do
  am=${pair%%:*}
  br=${pair#*:}
  # -H forces the FILE: prefix even for a single file, so parsing below is uniform.
  matches=$(grep -nHIwiE "$am" $FILES) || continue
  printf '%s\n' "$matches" | while IFS= read -r m; do
    # grep -n output is FILE:LINE:CONTENT; always print the human-readable line,
    # and in GitHub Actions also emit a workflow command so the line is annotated
    # inline on the diff (https://docs.github.com/actions/reference/workflow-commands).
    printf '%s   [American spelling; house style: "%s"]\n' "$m" "$br"
    if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
      file=${m%%:*}
      rest=${m#*:}
      line=${rest%%:*}
      printf '::error file=%s,line=%s::American spelling "%s"; house style: "%s"\n' \
        "$file" "$line" "$am" "$br"
    fi
  done
  found=1
done

if [ "$found" -ne 0 ]; then
  printf '\nDialect check failed. House style is British English, Oxford spelling (see CONTRIBUTING.md).\n'
  printf 'Adopted standards (CODE_OF_CONDUCT.md) are exempt. Oxford -ize is correct and is not flagged.\n'
  exit 1
fi
printf 'Dialect check passed: no American spellings found.\n'
