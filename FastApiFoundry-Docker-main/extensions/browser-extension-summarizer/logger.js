// logger.js

class Logger {
    constructor(logsKey = '__summarizer_logs__', maxLogs = 200) {
        this.logsKey = logsKey;
        this.maxLogs = maxLogs;
    }

    log(level, message, extra = null) {
        const timestamp = new Date().toISOString();
        const extraStr = extra ? (typeof extra === 'object' ? JSON.stringify(extra) : extra) : '';
        if (level === 'info')  (console.info  || console.log)(`[INFO]  [${timestamp}] ${message}`, extraStr);
        if (level === 'debug') (console.debug || console.log)(`[DEBUG] [${timestamp}] ${message}`, extraStr);
        if (level === 'warn')  console.warn(`[WARN]  [${timestamp}] ${message}`, extraStr);
        if (level === 'error') console.error(`[ERROR] [${timestamp}] ${message}`, extraStr);

        if (chrome?.storage?.local) {
            chrome.storage.local.get([this.logsKey], result => {
                const data = result[this.logsKey] || [];
                data.push({ timestamp, level, message, extra });
                if (data.length > this.maxLogs) data.splice(0, data.length - this.maxLogs);
                chrome.storage.local.set({ [this.logsKey]: data });
            });
        }
    }

    info(message, extra = null)  { this.log('info',  message, extra); }
    warn(message, extra = null)  { this.log('warn',  message, extra); }
    error(message, extra = null) { this.log('error', message, extra); }
    debug(message, extra = null) { this.log('debug', message, extra); }
}

const logger = new Logger();
export { Logger, logger };
