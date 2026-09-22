import "server-only";

import { supabase } from "@/lib/supabase/server";

export type Post = {
  id: string;
  title: string;
  author: string;
  content: string;
  views: number;
  createdAt: string;
};

type PostRow = {
  id: string;
  title: string;
  author: string;
  content: string;
  views: number;
  created_at: string;
};

function toPost(row: PostRow): Post {
  return {
    id: row.id,
    title: row.title,
    author: row.author,
    content: row.content,
    views: row.views,
    createdAt: row.created_at,
  };
}

export async function getPosts(): Promise<Post[]> {
  const { data, error } = await supabase
    .from("posts")
    .select("*")
    .order("created_at", { ascending: false });
  if (error) throw error;
  return (data as PostRow[]).map(toPost);
}

export async function getPost(id: string): Promise<Post | undefined> {
  const { data, error } = await supabase
    .from("posts")
    .select("*")
    .eq("id", id)
    .maybeSingle();
  if (error) throw error;
  return data ? toPost(data as PostRow) : undefined;
}

export async function incrementViews(id: string): Promise<void> {
  const { error } = await supabase.rpc("increment_post_views", {
    post_id: id,
  });
  if (error) throw error;
}

export async function createPost(input: {
  title: string;
  author: string;
  content: string;
}): Promise<Post> {
  const { data, error } = await supabase
    .from("posts")
    .insert({
      title: input.title,
      author: input.author,
      content: input.content,
    })
    .select("*")
    .single();
  if (error) throw error;
  return toPost(data as PostRow);
}

export async function updatePost(
  id: string,
  input: { title: string; author: string; content: string },
): Promise<void> {
  const { error } = await supabase
    .from("posts")
    .update({
      title: input.title,
      author: input.author,
      content: input.content,
    })
    .eq("id", id);
  if (error) throw error;
}

export async function deletePost(id: string): Promise<void> {
  const { error } = await supabase.from("posts").delete().eq("id", id);
  if (error) throw error;
}
