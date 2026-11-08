-- 폐기 가능한 로컬 GoTrue 통합 시험 DB의 초기화용이다.
create schema if not exists auth;
create extension if not exists pgcrypto;
alter role postgres set search_path to auth, public;
