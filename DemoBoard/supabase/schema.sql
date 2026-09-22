-- DemoBoard posts table
create table if not exists public.posts (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  author text not null,
  content text not null,
  views integer not null default 0,
  created_at timestamptz not null default now()
);

create index if not exists posts_created_at_idx on public.posts (created_at desc);

insert into public.posts (title, author, content, views)
values (
  'DemoBoard에 오신 것을 환영합니다',
  '관리자',
  '이곳은 Next.js와 shadcn/ui로 만든 데모 게시판입니다. 자유롭게 글을 작성해보세요.',
  3
)
on conflict do nothing;

create or replace function public.increment_post_views(post_id uuid)
returns void
language sql
as $$
  update public.posts set views = views + 1 where id = post_id;
$$;
