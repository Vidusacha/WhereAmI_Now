# Project WhereAmI_Now: Algorithm Flow (Phase 2 - Daily Discovery)

This document describes the exact step-by-step algorithm executed daily by `discovery/pipeline.py`.
These steps correspond directly to the log statements in `logs/audit.log`.

## Step 1: Fetching Daily News
- The pipeline calls the Gemini API to dynamically discover 5-7 relevant Israeli news RSS feeds (in Hebrew, English, and Russian).
- It parses the RSS feeds and aggregates the top fresh articles (titles and summaries).

## Step 2: Translating News to English
- The pipeline batches the aggregated articles.
- It calls the Gemini API to translate any non-English text to English, ensuring a unified context language.

## Step 3: LLM Analysis for New Axes and Party Statements
- All translated articles are concatenated into a single large prompt block.
- The prompt is sent to the **Local LLM (LM Studio / Mistral)**.
- The LLM's goal is to detect:
  1. **New Political Axes (Водоразделы)** based on the daily news context.
  2. **Party Statements** explicitly mapped to these axes.

## Step 4: Parsing LLM Output
- The pipeline extracts the JSON response from the local LLM.
- It cleans any potential markdown formatting (` ```json ... ``` `).
- It validates the presence of `new_axes` and `party_statements`.

## Step 5: Database Persistence
- New axes are inserted into the `axes_dictionary` table with `status = 'pending_review'`.
- Party names mentioned in the statements are checked against the `parties_registry`. If a party doesn't exist, it is created.
- The specific party statements are inserted into the `party_documents` table, linked to the corresponding party ID.
