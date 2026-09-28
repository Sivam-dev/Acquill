-- ============================================================================
-- Supabase RPC Functions for LearningTrack
-- Run these in Supabase SQL Editor after creating tables
-- ============================================================================

-- Function: check_topic_dependencies
-- Purpose: Check if prerequisite topics have low confidence or recent struggles
CREATE OR REPLACE FUNCTION check_topic_dependencies(p_topic_id uuid)
RETURNS TABLE (
  id uuid,
  name text,
  confidence_score double precision,
  recent_struggles bigint
)
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    t.id, 
    t.name, 
    t.confidence_score,
    COUNT(th.id) FILTER (WHERE th.event_type = 'struggled' 
                             AND th.created_at > NOW() - INTERVAL '7 days') as recent_struggles
  FROM topic_dependencies td
  JOIN topics t ON t.id = td.prerequisite_id
  LEFT JOIN topic_history th ON th.topic_id = t.id
  WHERE td.topic_id = p_topic_id
  GROUP BY t.id, t.name, t.confidence_score
  HAVING t.confidence_score < 50.0 
      OR COUNT(th.id) FILTER (WHERE th.event_type = 'struggled' 
                              AND th.created_at > NOW() - INTERVAL '7 days') > 0;
END;
$$;

-- Function: match_documents
-- Purpose: Vector similarity search for document retrieval
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(768),
  match_topic_id uuid,
  match_count int
)
RETURNS TABLE (content text, similarity float)
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
BEGIN
  RETURN QUERY
  SELECT documents.content, 
         (1 - (documents.embedding <=> query_embedding))::float as similarity
  FROM documents
  WHERE documents.topic_id = match_topic_id
  ORDER BY documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Function: get_digest_data
-- Purpose: Collect learning data for digest (topics touched, confidence, struggles)
CREATE OR REPLACE FUNCTION get_digest_data(
  p_start_date timestamptz,
  p_end_date timestamptz
)
RETURNS TABLE (
  topics_touched bigint,
  topic_name text,
  confidence_score double precision,
  struggle_count bigint
)
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
BEGIN
  RETURN QUERY
  WITH topics_count AS (
    SELECT COUNT(DISTINCT topic_id) as cnt
    FROM topic_history
    WHERE created_at BETWEEN p_start_date AND p_end_date
  ),
  topic_stats AS (
    SELECT 
      t.name as topic_name,
      t.confidence_score,
      COUNT(*) FILTER (WHERE th.event_type = 'struggled') as struggle_count
    FROM topic_history th
    JOIN topics t ON t.id = th.topic_id
    WHERE th.created_at BETWEEN p_start_date AND p_end_date
    GROUP BY t.id, t.name, t.confidence_score
  )
  SELECT 
    (SELECT cnt FROM topics_count) as topics_touched,
    ts.topic_name,
    ts.confidence_score,
    ts.struggle_count
  FROM topic_stats ts;
END;
$$;

-- Function: get_recurring_struggles
-- Purpose: Get topics with multiple struggles in time period
CREATE OR REPLACE FUNCTION get_recurring_struggles(
  p_start_date timestamptz,
  p_end_date timestamptz
)
RETURNS TABLE (topic_name text, struggle_count bigint)
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
BEGIN
  RETURN QUERY
  SELECT t.name, COUNT(*) as struggle_count
  FROM topic_history th
  JOIN topics t ON t.id = th.topic_id
  WHERE th.event_type = 'struggled'
    AND th.created_at BETWEEN p_start_date AND p_end_date
  GROUP BY t.name
  HAVING COUNT(*) > 1
  ORDER BY struggle_count DESC
  LIMIT 5;
END;
$$;

-- Function: get_pattern_analysis
-- Purpose: Analyze recurring mistake patterns
CREATE OR REPLACE FUNCTION get_pattern_analysis()
RETURNS TABLE (pattern text, frequency bigint, avg_days_between numeric)
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
BEGIN
  RETURN QUERY
  WITH pattern_occurrences AS (
    SELECT 
      jsonb_array_elements_text(t.mistake_patterns) as pattern,
      th.created_at
    FROM topic_history th
    JOIN topics t ON th.topic_id = t.id
    WHERE th.event_type = 'struggled'
      AND t.mistake_patterns IS NOT NULL
      AND jsonb_array_length(t.mistake_patterns) > 0
  ),
  pattern_stats AS (
    SELECT 
      po.pattern,
      COUNT(*) as frequency,
      CASE 
        WHEN COUNT(*) > 1 THEN
          EXTRACT(EPOCH FROM (MAX(po.created_at) - MIN(po.created_at))) / 86400 / (COUNT(*) - 1)
        ELSE 0
      END as avg_days_between
    FROM pattern_occurrences po
    GROUP BY po.pattern
    HAVING COUNT(*) >= 2
  )
  SELECT ps.pattern, ps.frequency, ps.avg_days_between
  FROM pattern_stats ps
  ORDER BY ps.frequency DESC, ps.avg_days_between ASC
  LIMIT 10;
END;
$$;
