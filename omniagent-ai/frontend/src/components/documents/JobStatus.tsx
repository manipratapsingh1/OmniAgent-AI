import React from "react";
import { jobService } from "../../api/jobService";
import { usePolling } from "../../hooks/usePolling";

export default function JobStatus({ jobId }: { jobId: number | null }) {
  const fetcher = async () => {
    if (!jobId) throw new Error("No job id");
    return await jobService.getJob(jobId);
  };

  const { data, loading } = usePolling<any>(fetcher, { interval: 2000, enabled: !!jobId });

  if (!jobId) return null;

  const job = data;

  return (
    <div className="mt-3">
      <div className="text-sm text-zinc-300">Upload job: {jobId}</div>
      <div className="mt-2 w-full bg-slate-700 rounded-full h-2 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
          style={{ width: `${job?.progress ?? 0}%`, transition: "width 0.5s" }}
        />
      </div>
      <div className="mt-2 text-xs text-zinc-400">
        Status: {job?.status ?? (loading ? "checking..." : "pending")}
        {job?.error ? ` — ${job.error}` : ""}
      </div>
    </div>
  );
}
