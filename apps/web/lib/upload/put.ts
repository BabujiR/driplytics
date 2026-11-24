/**
 * Send the file straight to object storage with the presigned URL (ADR 0019): the file never passes
 * through the web server or the API. XMLHttpRequest, because fetch() can't report upload progress.
 */
import type { UploadTarget } from "@driplytics/contracts";

export class UploadError extends Error {}

export function putWithProgress(
  target: UploadTarget,
  file: Blob,
  onProgress: (fraction: number) => void,
  signal?: AbortSignal,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(target.method, target.url);
    for (const [k, v] of Object.entries(target.headers)) xhr.setRequestHeader(k, v);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(e.loaded / e.total);
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress(1);
        resolve();
      } else {
        reject(
          new UploadError(
            xhr.status === 403
              ? "Storage refused the upload (the upload link may have expired). Start again."
              : `Storage answered HTTP ${xhr.status}.`,
          ),
        );
      }
    };
    xhr.onerror = () =>
      reject(new UploadError("The upload could not reach object storage. Check your connection and try again."));
    xhr.onabort = () => reject(new UploadError("Upload cancelled."));
    signal?.addEventListener("abort", () => xhr.abort(), { once: true });
    xhr.send(file);
  });
}
