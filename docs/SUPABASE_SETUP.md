# Supabase Setup Guide

## Prerequisites
- Supabase account (free tier works)
- Tables created in Supabase with `user_id` columns and RLS enabled

## Step 1: Create SQL Functions

Go to your Supabase dashboard → SQL Editor and run all functions from `supabase_functions.sql`.

These functions are needed for:
- **check_topic_dependencies**: Checks prerequisite topics for confidence issues
- **match_documents**: Vector similarity search for document retrieval
- **get_digest_data**: Collects learning metrics for weekly digests
- **get_recurring_struggles**: Identifies topics with repeated struggles
- **get_pattern_analysis**: Analyzes recurring mistake patterns

## Step 2: Configure Environment

Make sure your `.env` file has:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_publishable_anon_key_here
```

**Security Note**: Using the publishable (anon) key is safe because:
- RLS (Row Level Security) is enabled on all tables
- Each user only sees their own data
- The publishable key is designed for client-side use

## Step 3: Test Connection

Run the check script:

```powershell
python check_schema.py
```

## How RLS Works

With RLS enabled, Supabase automatically filters all queries by `user_id`:

```python
# You write:
supabase.table('topics').select('*').execute()

# Supabase automatically adds:
# WHERE user_id = auth.uid()
```

No need to manually add `user_id` to queries - RLS handles it!

## Migration from PostgreSQL

The conversion replaced:
- ❌ `psycopg` connections → ✅ `supabase` client
- ❌ `cur.execute()` → ✅ `.table().select()/.insert()/.update()`
- ❌ Raw SQL → ✅ Query builder + RPC functions for complex queries
- ❌ Manual user_id filtering → ✅ Automatic RLS filtering

## Troubleshooting

### "relation does not exist" error
- Check that tables are created in Supabase
- Ensure you're using the correct project URL

### "permission denied" error
- Verify RLS policies are set up correctly
- Check that `user_id` columns exist in all tables

### Vector search not working
- Ensure `pgvector` extension is enabled
- Run the `match_documents` function creation SQL
- Check that embeddings are being stored correctly
