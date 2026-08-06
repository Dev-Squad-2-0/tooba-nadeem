## Deepgram STT Notes

Issue:
- Streaming worked but transcripts were mostly empty.

Root Cause:
- Deepgram configuration was using an unsuitable model/language combination.
- Domain-specific acronyms (e.g. DHA) also required keyterm prompting.

Resolution:
- Model: nova-3
- Language: ur
- Added keyterms for real estate terminology.

Result:
- Verified accurate transcription of real Pakistani Urdu speech.
