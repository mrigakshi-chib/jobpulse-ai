"use client";

import { useEffect, useState } from "react";

type JobStats = {
  total_jobs: number;
  high_score_jobs: number;
  follow_ups_due: number;
  status_counts: Record<string, number>;
  source_counts: Record<string, number>;
};

type Job = {
  id: number;
  source: string;
  title: string;
  company: string;
  location?: string | null;
  job_url: string;
  apply_url?: string | null;
  status: string;
  score: number;
  follow_up_date?: string | null;
  resume_version?: string | null;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default function Home() {
  const [stats, setStats] = useState<JobStats | null>(null);
  const [fullTimeJobs, setFullTimeJobs] = useState<Job[]>([]);
  const [internshipJobs, setInternshipJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [statsResponse, fullTimeResponse, internshipResponse] =
          await Promise.all([
            fetch(`${API_URL}/jobs/stats`),
            fetch(
  `${API_URL}/jobs/?min_score=65&location=India&target_role=software&exclude_internships=true&exclude_testing_roles=true&exclude_non_target_roles=true`
),
            fetch(
  `${API_URL}/jobs/?min_score=60&location=India&search=intern&exclude_testing_roles=true&exclude_non_target_roles=true`
),
          ]);

        const statsData = await statsResponse.json();
        const fullTimeData = await fullTimeResponse.json();
        const internshipData = await internshipResponse.json();

        setStats(statsData);
        setFullTimeJobs(fullTimeData);
        setInternshipJobs(internshipData);
      } catch (error) {
        console.error("Failed to load dashboard", error);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 text-white p-8">
        <p>Loading JobPulse AI dashboard...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-8">
          <p className="text-sm text-emerald-400 font-medium">JobPulse AI</p>
          <h1 className="text-3xl font-bold mt-2">
            Fresher Job Discovery Dashboard
          </h1>
          <p className="text-slate-400 mt-2">
            Track fresher-friendly software roles, internships, applications,
            and follow-ups.
          </p>
        </div>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <StatCard label="Total jobs" value={stats.total_jobs} />
            <StatCard label="High-score jobs" value={stats.high_score_jobs} />
            <StatCard label="Follow-ups due" value={stats.follow_ups_due} />
            <StatCard
              label="Applied"
              value={stats.status_counts.applied ?? 0}
            />
          </div>
        )}

        <JobSection
          title="Full-time priority jobs"
          description="Fresher-friendly full-time roles in India with score 65 or above."
          jobs={fullTimeJobs}
        />

        <div className="mt-8">
          <JobSection
            title="Internship / conversion opportunities"
            description="Internships in India that may be useful if they have PPO or full-time conversion potential."
            jobs={internshipJobs}
          />
        </div>
      </section>
    </main>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="text-3xl font-bold mt-2">{value}</p>
    </div>
  );
}

function JobSection({
  title,
  description,
  jobs,
}: {
  title: string;
  description: string;
  jobs: Job[];
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
      <div className="p-5 border-b border-slate-800">
        <h2 className="text-xl font-semibold">{title}</h2>
        <p className="text-sm text-slate-400 mt-1">{description}</p>
      </div>

      <div className="divide-y divide-slate-800">
        {jobs.length === 0 ? (
          <p className="p-5 text-slate-400">No jobs found in this section yet.</p>
        ) : (
          jobs.map((job) => <JobRow key={job.id} job={job} />)
        )}
      </div>
    </div>
  );
}

function JobRow({ job }: { job: Job }) {
  return (
    <div className="p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <span className="text-xs bg-emerald-500/10 text-emerald-300 px-2 py-1 rounded-full">
            Score {job.score}
          </span>
          <span className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded-full">
            {job.status}
          </span>
          <span className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded-full">
            {job.source}
          </span>
        </div>

        <h3 className="font-semibold text-lg">{job.title}</h3>
        <p className="text-slate-400 text-sm mt-1">
          {job.company} · {job.location ?? "Location not specified"}
        </p>

        {job.follow_up_date && (
          <p className="text-sm text-yellow-300 mt-2">
            Follow up: {job.follow_up_date}
          </p>
        )}
      </div>

      <a
        href={job.apply_url || job.job_url}
        target="_blank"
        rel="noreferrer"
        className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold px-4 py-2 rounded-xl text-center"
      >
        Apply
      </a>
    </div>
  );
}