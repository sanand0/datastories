#!/usr/bin/bash

while IFS=$'\t' read -r CAPTION PROMPT; do
  target="$(echo "$CAPTION" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g').webp"
  if [[ -f "$target" ]]; then
    continue
  fi
  echo "$target"

  cat <<EOF > .tmp.request.json
{
  "contents": [
    {
      "role": "user",
      "parts": [
        { "inlineData": { "mimeType": "image/jpeg", "data": "$(base64 -w 0 anand.webp)" } },
        { "text": $(echo "Draw a single-panel square comic image in Amar Chitra Katha style in a Vipassana meditation center. Draw the protagonist EXACTLY like the attached photo, wearing a T-shirt. No text in the image. $PROMPT" | jq -R -c) }
      ]
    }
  ],
  "generationConfig": { "responseModalities": ["IMAGE", "TEXT"] }
}
EOF

  curl --silent "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:streamGenerateContent?key=$GEMINI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "@.tmp.request.json" > .tmp.output.json

  jq -r 'first(..|.inlineData?.data?|select(.!=null))' .tmp.output.json | base64 -d > .tmp.panel.jpg

  cwebp -q 5 -m 6 -pass 10 -af -mt .tmp.panel.jpg -quiet -o "$target"
done < prompts.txt

rm .tmp.*
