"use client";

import { useEffect, useMemo, useState } from "react";

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

type TabKey = "priority" | "saved" | "applied" | "internships" | "not_interested";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

const PRIORITY_JOBS_URL =
  `${API_URL}/jobs/?status=new&min_score=65&location=India` +
  `&target_role=software&exclude_internships=true` +
  `&exclude_testing_roles=true&exclude_non_target_roles=true` +
  `&exclude_not_relevant=true`;

const INTERNSHIP_JOBS_URL =
  `${API_URL}/jobs/?status=new&min_score=60&location=India&search=intern` +
  `&exclude_testing_roles=true&exclude_non_target_roles=true` +
  `&exclude_not_relevant=true`;

const SAVED_JOBS_URL = `${API_URL}/jobs/?status=saved&exclude_not_relevant=true`;
const APPLIED_JOBS_URL = `${API_URL}/jobs/?status=applied&exclude_not_relevant=true`;
const NOT_INTERESTED_JOBS_URL = `${API_URL}/jobs/?status=not_relevant`;

export default function Home() {
  const [stats, setStats] = useState<JobStats | null>(null);
  const [priorityJobs, setPriorityJobs] = useState<Job[]>([]);
  const [internshipJobs, setInternshipJobs] = useState<Job[]>([]);
  const [savedJobs, setSavedJobs] = useState<Job[]>([]);
  const [appliedJobs, setAppliedJobs] = useState<Job[]>([]);
  const [notInterestedJobs, setNotInterestedJobs] = useState<Job[]>([]);
  const [activeTab, setActiveTab] = useState<TabKey>("priority");
  const [loading, setLoading] = useState(true);
  const [updatingJobId, setUpdatingJobId] = useState<number | null>(null);

  async function loadDashboard() {
    try {
      const [
        statsResponse,
        priorityResponse,
        internshipResponse,
        savedResponse,
        appliedResponse,
        notInterestedResponse,
      ] = await Promise.all([
        fetch(`${API_URL}/jobs/stats`),
        fetch(PRIORITY_JOBS_URL),
        fetch(INTERNSHIP_JOBS_URL),
        fetch(SAVED_JOBS_URL),
        fetch(APPLIED_JOBS_URL),
        fetch(NOT_INTERESTED_JOBS_URL),
      ]);

      const statsData = await statsResponse.json();
      const priorityData = await priorityResponse.json();
      const internshipData = await internshipResponse.json();
      const savedData = await savedResponse.json();
      const appliedData = await appliedResponse.json();
      const notInterestedData = await notInterestedResponse.json();

      setStats(statsData);
      setPriorityJobs(priorityData);
      setInternshipJobs(internshipData);
      setSavedJobs(savedData);
      setAppliedJobs(appliedData);
      setNotInterestedJobs(notInterestedData);
    } catch (error) {
      console.error("Failed to load dashboard", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  async function updateJobStatus(jobId: number, status: string) {
    try {
      setUpdatingJobId(jobId);

      const response = await fetch(`${API_URL}/jobs/${jobId}/status`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status }),
      });

      if (!response.ok) {
        throw new Error("Failed to update job status");
      }

      await loadDashboard();
    } catch (error) {
      console.error("Failed to update job status", error);
      alert("Could not update job status. Please try again.");
    } finally {
      setUpdatingJobId(null);
    }
  }

  const tabs = useMemo(
    () => [
      {
        key: "priority" as const,
        label: "New Priority",
        count: priorityJobs.length,
        title: "New full-time priority jobs",
        description:
          "Fresh new full-time roles in India that match your target software roles.",
        emptyText: "No new priority jobs found right now.",
        jobs: priorityJobs,
      },
      {
        key: "saved" as const,
        label: "Saved",
        count: savedJobs.length,
        title: "Saved jobs",
        description: "Jobs you saved to review or apply to later.",
        emptyText: "No saved jobs yet.",
        jobs: savedJobs,
      },
      {
        key: "applied" as const,
        label: "Applied",
        count: appliedJobs.length,
        title: "Applied jobs",
        description: "Jobs you have already applied to.",
        emptyText: "No applied jobs yet.",
        jobs: appliedJobs,
      },
      {
        key: "internships" as const,
        label: "Internships",
        count: internshipJobs.length,
        title: "Internship / conversion opportunities",
        description:
          "Internships in India that may be useful if they have PPO or full-time conversion potential.",
        emptyText: "No internship opportunities found right now.",
        jobs: internshipJobs,
      },
      {
        key: "not_interested" as const,
        label: "Not Interested",
        count: notInterestedJobs.length,
        title: "Not interested",
        description:
          "Jobs you marked as not relevant. They are hidden from your active dashboard but kept here for review.",
        emptyText: "No jobs marked as not interested yet.",
        jobs: notInterestedJobs,
      },
    ],
    [priorityJobs, savedJobs, appliedJobs, internshipJobs, notInterestedJobs]
  );

  const activeTabData = tabs.find((tab) => tab.key === activeTab) ?? tabs[0];

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

        <div className="mb-5 flex flex-wrap gap-2">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.key;

            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={
                  isActive
                    ? "bg-emerald-500 text-slate-950 font-semibold px-4 py-2 rounded-xl"
                    : "bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 px-4 py-2 rounded-xl"
                }
              >
                {tab.label}
                <span className="ml-2 text-xs opacity-80">({tab.count})</span>
              </button>
            );
          })}
        </div>

        <JobSection
          title={activeTabData.title}
          description={activeTabData.description}
          jobs={activeTabData.jobs}
          emptyText={activeTabData.emptyText}
          updatingJobId={updatingJobId}
          onStatusChange={updateJobStatus}
        />
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
  emptyText,
  updatingJobId,
  onStatusChange,
}: {
  title: string;
  description: string;
  jobs: Job[];
  emptyText: string;
  updatingJobId: number | null;
  onStatusChange: (jobId: number, status: string) => void;
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
      <div className="p-5 border-b border-slate-800">
        <h2 className="text-xl font-semibold">{title}</h2>
        <p className="text-sm text-slate-400 mt-1">{description}</p>
      </div>

      <div className="divide-y divide-slate-800">
        {jobs.length === 0 ? (
          <p className="p-5 text-slate-400">{emptyText}</p>
        ) : (
          jobs.map((job) => (
            <JobRow
              key={job.id}
              job={job}
              updatingJobId={updatingJobId}
              onStatusChange={onStatusChange}
            />
          ))
        )}
      </div>
    </div>
  );
}

function JobRow({
  job,
  updatingJobId,
  onStatusChange,
}: {
  job: Job;
  updatingJobId: number | null;
  onStatusChange: (jobId: number, status: string) => void;
}) {
  const isUpdating = updatingJobId === job.id;

  function handleNotRelevant() {
    const confirmed = window.confirm(
      "Move this job to Not Interested? You can still find it in the Not Interested tab."
    );

    if (confirmed) {
      onStatusChange(job.id, "not_relevant");
    }
  }

  return (
    <div className="p-5 flex flex-col gap-4">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
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

      <div className="flex flex-wrap gap-2">
        <button
          disabled={isUpdating}
          onClick={() => onStatusChange(job.id, "saved")}
          className="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-100 px-3 py-2 rounded-xl text-sm"
        >
          Save
        </button>

        <button
          disabled={isUpdating}
          onClick={() => onStatusChange(job.id, "applied")}
          className="bg-blue-500/20 hover:bg-blue-500/30 disabled:opacity-50 text-blue-200 px-3 py-2 rounded-xl text-sm"
        >
          Mark Applied
        </button>

        <button
          disabled={isUpdating}
          onClick={handleNotRelevant}
          className="bg-red-500/20 hover:bg-red-500/30 disabled:opacity-50 text-red-200 px-3 py-2 rounded-xl text-sm"
        >
          Not Relevant
        </button>
      </div>
    </div>
  );
}