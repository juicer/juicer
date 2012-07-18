;;; Some simple defun's to speed up the process of adding logging
;;; entries to juicer source code.
;;;
;;; Include in your ~/.emacs.d directory and load, or add directly to
;;; your ~/.emacs file.
;;;
;;; Example: M-x juicer-log-info<RET>
;;; Message (Don't forget quotes!):"Working on repo: %s", repo<RET>
;;;
;;; Would insert: juicer.utils.Log.log_info("Working on repo: %s", repo)


(defun juicer-log(level msg)
  "Write the python statement for adding a log entry"
  (save-excursion
    (indent-relative-maybe)
    (insert "juicer.utils.Log.log_" level "(" msg ")")))

(defun juicer-log-debug (message)
  (interactive "sMessage (Don't forget quotes!):\n")
  (juicer-log "debug" message))

(defun juicer-log-error (message)
  (interactive "sMessage (Don't forget quotes!):\n")
  (juicer-log "error" message))

(defun juicer-log-warn (message)
  (interactive "sMessage (Don't forget quotes!):\n")
  (juicer-log "warn" message))

(defun juicer-log-info (message)
  (interactive "sMessage (Don't forget quotes!):\n")
  (juicer-log "info" message))

(defun juicer-log-notice (message)
  (interactive "sMessage (Don't forget quotes!):\n")
  (juicer-log "notice" message))
