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
  applied_at?: string | null;
  follow_up_date?: string | null;
  notes?: string | null;
  resume_version?: string | null;
};

type TabKey =
  | "all_new"
  | "priority"
  | "saved"
  | "applied"
  | "internships"
  | "not_interested";

type ApplicationUpdateInput = {
  follow_up_date: string | null;
  resume_version: string | null;
  notes: string | null;
};

type ScrapeRunResult = {
  message?: string;
  total_fetched?: number;
  total_inserted?: number;
  inserted?: number;
  inserted_jobs?: number;
  duplicates?: number;
  skipped_duplicates?: number;
  total_skipped_low_quality?: number;
  skipped_low_quality?: number;
  enabled_sources?: number;
  result?: {
    total_fetched?: number;
    total_inserted?: number;
    inserted?: number;
    inserted_jobs?: number;
    duplicates?: number;
    skipped_duplicates?: number;
  };
};

type LastScrapeSummary = {
  jobspyFetched: number;
  jobspyInserted: number;
  jobspySkippedLowQuality: number;
  jobspySkippedDuplicates: number;
  jobspySkippedLowScore: number;
  companyFetched: number;
  companyInserted: number;
  companySkippedNonTarget: number;
  companySkippedDuplicates: number;
  companySkippedLowScore: number;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL;

const TARGET_LOCATIONS =
  "India,Remote,Work from home,WFH,Bangalore,Bengaluru,Hyderabad,Pune,Mumbai,Navi Mumbai,Delhi,New Delhi,Delhi NCR,NCR,Noida,Gurgaon,Gurugram";

const ALL_NEW_MATCHES_URL =
  `${API_URL}/jobs/?status=new&min_score=50` +
  `&locations=${encodeURIComponent(TARGET_LOCATIONS)}` +
  `&exclude_testing_roles=true&exclude_non_target_roles=true` +
  `&exclude_not_relevant=true`;

const PRIORITY_JOBS_URL =
  `${API_URL}/jobs/?status=new&min_score=65` +
  `&locations=${encodeURIComponent(TARGET_LOCATIONS)}` +
  `&target_role=software&exclude_internships=true` +
  `&exclude_testing_roles=true&exclude_non_target_roles=true` +
  `&exclude_not_relevant=true`;

const INTERNSHIP_JOBS_URL =
  `${API_URL}/jobs/?status=new&min_score=40&search=intern` +
  `&locations=${encodeURIComponent(TARGET_LOCATIONS)}` +
  `&exclude_testing_roles=true&exclude_non_target_roles=true` +
  `&exclude_not_relevant=true`;

const SAVED_JOBS_URL = `${API_URL}/jobs/?status=saved&exclude_not_relevant=true`;
const APPLIED_JOBS_URL = `${API_URL}/jobs/?status=applied&exclude_not_relevant=true`;
const NOT_INTERESTED_JOBS_URL = `${API_URL}/jobs/?status=not_relevant`;

export default function Home() {
  const [stats, setStats] = useState<JobStats | null>(null);

  const [allNewJobs, setAllNewJobs] = useState<Job[]>([]);
  const [priorityJobs, setPriorityJobs] = useState<Job[]>([]);
  const [internshipJobs, setInternshipJobs] = useState<Job[]>([]);
  const [savedJobs, setSavedJobs] = useState<Job[]>([]);
  const [appliedJobs, setAppliedJobs] = useState<Job[]>([]);
  const [notInterestedJobs, setNotInterestedJobs] = useState<Job[]>([]);

  const [activeTab, setActiveTab] = useState<TabKey>("all_new");
  const [loading, setLoading] = useState(true);
  const [updatingJobId, setUpdatingJobId] = useState<number | null>(null);

  const [scrapeRunning, setScrapeRunning] = useState(false);
  const [scrapeMessage, setScrapeMessage] = useState<string | null>(null);

  const [lastScrapeSummary, setLastScrapeSummary] =
  useState<LastScrapeSummary | null>(null);

  async function loadDashboard() {
    try {
      const [
        statsResponse,
        allNewResponse,
        priorityResponse,
        internshipResponse,
        savedResponse,
        appliedResponse,
        notInterestedResponse,
      ] = await Promise.all([
        fetch(`${API_URL}/jobs/stats`),
        fetch(ALL_NEW_MATCHES_URL),
        fetch(PRIORITY_JOBS_URL),
        fetch(INTERNSHIP_JOBS_URL),
        fetch(SAVED_JOBS_URL),
        fetch(APPLIED_JOBS_URL),
        fetch(NOT_INTERESTED_JOBS_URL),
      ]);

      const statsData = await statsResponse.json();
      const allNewData = await allNewResponse.json();
      const priorityData = await priorityResponse.json();
      const internshipData = await internshipResponse.json();
      const savedData = await savedResponse.json();
      const appliedData = await appliedResponse.json();
      const notInterestedData = await notInterestedResponse.json();

      setStats(statsData);
      setAllNewJobs(allNewData);
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

  async function updateJobApplication(
    jobId: number,
    data: ApplicationUpdateInput
  ) {
    try {
      setUpdatingJobId(jobId);

      const response = await fetch(`${API_URL}/jobs/${jobId}/application`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error("Failed to update application details");
      }

      await loadDashboard();
    } catch (error) {
      console.error("Failed to update application details", error);
      alert("Could not save application details. Please try again.");
    } finally {
      setUpdatingJobId(null);
    }
  }

  async function runFreshJobsSearch() {
  try {
    setScrapeRunning(true);
    setScrapeMessage("Searching JobSpy and company career pages...");

    const [jobspyResponse, companyResponse] = await Promise.all([
      fetch(`${API_URL}/scheduler/run-now`, {
        method: "POST",
      }),
      fetch(`${API_URL}/scrape/companies/?min_score=60`, {
        method: "POST",
      }),
    ]);

    if (!jobspyResponse.ok) {
      throw new Error("Failed to run JobSpy scraper");
    }

    if (!companyResponse.ok) {
      throw new Error("Failed to run company career-page scraper");
    }

    const jobspyData = await jobspyResponse.json();
    const companyData = await companyResponse.json();

    const jobspyFetched = jobspyData.total_fetched ?? 0;
    const jobspyInserted =
      jobspyData.inserted ?? jobspyData.total_inserted ?? 0;

    const jobspySkippedLowQuality =
      jobspyData.total_skipped_low_quality ??
      jobspyData.skipped_low_quality ??
      0;

    const jobspySkippedDuplicates =
      jobspyData.total_skipped_duplicates ?? 0;

    const jobspySkippedLowScore =
      jobspyData.total_skipped_low_score ?? 0;

    const companyFetched = companyData.total_fetched ?? 0;
    const companyInserted =
      companyData.inserted ?? companyData.total_inserted ?? 0;

    const companySkippedNonTarget =
      companyData.total_skipped_non_target_role ??
      companyData.total_skipped_not_fresher_friendly ??
      0;

    const companySkippedDuplicates =
      companyData.total_skipped_duplicates ?? 0;

    const companySkippedLowScore =
      companyData.total_skipped_low_score ?? 0;

    await loadDashboard();

    setLastScrapeSummary({
      jobspyFetched,
      jobspyInserted,
      jobspySkippedLowQuality,
      jobspySkippedDuplicates,
      jobspySkippedLowScore,
      companyFetched,
      companyInserted,
      companySkippedNonTarget,
      companySkippedDuplicates,
      companySkippedLowScore,
    });

    setScrapeMessage("Fresh search complete. Dashboard refreshed.");
  } catch (error) {
    console.error("Failed to run fresh jobs search", error);
    setScrapeMessage("Could not run fresh jobs search. Please try again.");
  } finally {
    setScrapeRunning(false);
  }
}

  const tabs = useMemo(
    () => [
      {
        key: "all_new" as const,
        label: "All New Matches",
        count: allNewJobs.length,
        title: "All new matches",
        description:
          "A broader review list of newly found jobs from your target Indian and remote locations.",
        emptyText: "No new matches found right now.",
        jobs: allNewJobs,
      },
      {
        key: "priority" as const,
        label: "New Priority",
        count: priorityJobs.length,
        title: "New full-time priority jobs",
        description:
          "Strictly filtered full-time roles that best match your software job target.",
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
          "Internships that may be useful if they have PPO or full-time conversion potential.",
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
    [
      allNewJobs,
      priorityJobs,
      savedJobs,
      appliedJobs,
      internshipJobs,
      notInterestedJobs,
    ]
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
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm text-emerald-400 font-medium">JobPulse AI</p>
            <h1 className="text-3xl font-bold mt-2">
              Fresher Job Discovery Dashboard
            </h1>
            <p className="text-slate-400 mt-2">
              Track fresher-friendly software roles, internships, applications,
              and follow-ups.
            </p>

            {scrapeMessage && (
              <p className="text-sm text-slate-300 mt-3">{scrapeMessage}</p>
            )}
          </div>

          <button
            onClick={runFreshJobsSearch}
            disabled={scrapeRunning}
            className="bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-semibold px-5 py-3 rounded-xl"
          >
            {scrapeRunning ? "Searching..." : "Find Fresh Jobs Now"}
          </button>
        </div>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <StatCard label="Total jobs" value={stats.total_jobs} />
            <StatCard label="Active matches" value={allNewJobs.length} />
            <StatCard label="Saved" value={savedJobs.length} />
            <StatCard label="Applied" value={appliedJobs.length} />
          </div>
        )}

        {lastScrapeSummary && (
          <ScrapeSummaryPanel summary={lastScrapeSummary} />
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
          onApplicationUpdate={updateJobApplication}
          showTrackingForm={activeTab !== "not_interested"}
          showNotRelevantButton={activeTab !== "not_interested"}
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
function ScrapeSummaryPanel({
  summary,
}: {
  summary: LastScrapeSummary;
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-8">
      <div className="mb-4">
        <h2 className="text-lg font-semibold">Last scrape summary</h2>
        <p className="text-sm text-slate-400 mt-1">
          This helps you understand whether jobs were found, inserted, skipped
          as duplicates, or rejected by filters.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl bg-slate-950/60 border border-slate-800 p-4">
          <h3 className="font-semibold mb-3">JobSpy</h3>

          <div className="grid grid-cols-2 gap-3 text-sm">
            <SummaryItem label="Fetched" value={summary.jobspyFetched} />
            <SummaryItem label="Inserted" value={summary.jobspyInserted} />
            <SummaryItem
              label="Low quality"
              value={summary.jobspySkippedLowQuality}
            />
            <SummaryItem
              label="Duplicates"
              value={summary.jobspySkippedDuplicates}
            />
            <SummaryItem
              label="Low score"
              value={summary.jobspySkippedLowScore}
            />
          </div>
        </div>

        <div className="rounded-xl bg-slate-950/60 border border-slate-800 p-4">
          <h3 className="font-semibold mb-3">Company pages</h3>

          <div className="grid grid-cols-2 gap-3 text-sm">
            <SummaryItem label="Fetched" value={summary.companyFetched} />
            <SummaryItem label="Inserted" value={summary.companyInserted} />
            <SummaryItem
              label="Non-target"
              value={summary.companySkippedNonTarget}
            />
            <SummaryItem
              label="Duplicates"
              value={summary.companySkippedDuplicates}
            />
            <SummaryItem
              label="Low score"
              value={summary.companySkippedLowScore}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function SummaryItem({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div>
      <p className="text-slate-500">{label}</p>
      <p className="text-xl font-semibold">{value}</p>
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
  onApplicationUpdate,
  showTrackingForm,
  showNotRelevantButton,
}: {
  title: string;
  description: string;
  jobs: Job[];
  emptyText: string;
  updatingJobId: number | null;
  onStatusChange: (jobId: number, status: string) => void;
  onApplicationUpdate: (jobId: number, data: ApplicationUpdateInput) => void;
  showTrackingForm: boolean;
  showNotRelevantButton: boolean;
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
              onApplicationUpdate={onApplicationUpdate}
              showTrackingForm={showTrackingForm}
              showNotRelevantButton={showNotRelevantButton}
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
  onApplicationUpdate,
  showTrackingForm,
  showNotRelevantButton,
}: {
  job: Job;
  updatingJobId: number | null;
  onStatusChange: (jobId: number, status: string) => void;
  onApplicationUpdate: (jobId: number, data: ApplicationUpdateInput) => void;
  showTrackingForm: boolean;
  showNotRelevantButton: boolean;
}) {
  const isUpdating = updatingJobId === job.id;
  const [showAppliedPrompt, setShowAppliedPrompt] = useState(false);

  function handleApplyClick() {
    const applyUrl = job.apply_url || job.job_url;

    window.open(applyUrl, "_blank", "noopener,noreferrer");
    setShowAppliedPrompt(true);
  }

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

          <JobTrackingSummary job={job} />
        </div>

        <button
          disabled={isUpdating}
          onClick={handleApplyClick}
          className="bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-semibold px-4 py-2 rounded-xl text-center"
        >
          Apply
        </button>
      </div>

      {showAppliedPrompt && job.status !== "applied" && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
          <p className="text-sm text-emerald-100 mb-3">
            Did you complete the application for this job?
          </p>

          <div className="flex flex-wrap gap-2">
            <button
              disabled={isUpdating}
              onClick={() => {
                onStatusChange(job.id, "applied");
                setShowAppliedPrompt(false);
              }}
              className="bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-semibold px-3 py-2 rounded-xl text-sm"
            >
              Yes, mark applied
            </button>

            <button
              disabled={isUpdating}
              onClick={() => setShowAppliedPrompt(false)}
              className="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-100 px-3 py-2 rounded-xl text-sm"
            >
              Not yet
            </button>
          </div>
        </div>
      )}

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

        {showNotRelevantButton && (
          <button
            disabled={isUpdating}
            onClick={handleNotRelevant}
            className="bg-red-500/20 hover:bg-red-500/30 disabled:opacity-50 text-red-200 px-3 py-2 rounded-xl text-sm"
          >
            Not Relevant
          </button>
        )}
      </div>

      {showTrackingForm ? (
        <JobTrackingForm
          job={job}
          isUpdating={isUpdating}
          onApplicationUpdate={onApplicationUpdate}
        />
      ) : (
        <p className="text-sm text-slate-400">
          This job is archived as Not Interested. Use Save or Mark Applied to
          move it back into your active workflow.
        </p>
      )}
    </div>
  );
}

function JobTrackingSummary({ job }: { job: Job }) {
  const hasTrackingDetails =
    job.applied_at || job.follow_up_date || job.resume_version || job.notes;

  if (!hasTrackingDetails) {
    return null;
  }

  return (
    <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-sm text-slate-300 space-y-1">
      {job.applied_at && <p>Applied on: {job.applied_at.slice(0, 10)}</p>}
      {job.follow_up_date && <p>Follow up: {job.follow_up_date}</p>}
      {job.resume_version && <p>Resume: {job.resume_version}</p>}
      {job.notes && <p>Notes: {job.notes}</p>}
    </div>
  );
}

function JobTrackingForm({
  job,
  isUpdating,
  onApplicationUpdate,
}: {
  job: Job;
  isUpdating: boolean;
  onApplicationUpdate: (jobId: number, data: ApplicationUpdateInput) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [followUpDate, setFollowUpDate] = useState(job.follow_up_date ?? "");
  const [resumeVersion, setResumeVersion] = useState(job.resume_version ?? "");
  const [notes, setNotes] = useState(job.notes ?? "");

  useEffect(() => {
    setFollowUpDate(job.follow_up_date ?? "");
    setResumeVersion(job.resume_version ?? "");
    setNotes(job.notes ?? "");
  }, [job.id, job.follow_up_date, job.resume_version, job.notes]);

  function handleSaveTracking() {
    onApplicationUpdate(job.id, {
      follow_up_date: followUpDate || null,
      resume_version: resumeVersion.trim() || null,
      notes: notes.trim() || null,
    });

    setIsOpen(false);
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/40">
      <button
        onClick={() => setIsOpen((current) => !current)}
        className="w-full text-left px-4 py-3 text-sm text-slate-300 hover:bg-slate-800/60 rounded-xl"
      >
        {isOpen ? "Hide tracking details" : "Add / edit tracking details"}
      </button>

      {isOpen && (
        <div className="p-4 pt-0 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1">
              Follow-up date
            </label>
            <input
              type="date"
              value={followUpDate}
              onChange={(event) => setFollowUpDate(event.target.value)}
              className="w-full rounded-xl bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-white"
            />
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1">
              Resume version
            </label>
            <input
              type="text"
              value={resumeVersion}
              onChange={(event) => setResumeVersion(event.target.value)}
              placeholder="Example: Resume v1 backend"
              className="w-full rounded-xl bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-white"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs text-slate-400 mb-1">Notes</label>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Example: Applied through careers page. Need to message recruiter on LinkedIn."
              rows={3}
              className="w-full rounded-xl bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-white"
            />
          </div>

          <div className="md:col-span-2">
            <button
              disabled={isUpdating}
              onClick={handleSaveTracking}
              className="bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-semibold px-4 py-2 rounded-xl text-sm"
            >
              Save Tracking Details
            </button>
          </div>
        </div>
      )}
    </div>
  );
}