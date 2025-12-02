((python-mode
  ;; Activar automáticamente .venv de uv
  (python-shell-virtualenv-root . ".venv")

  ;; Pyright: decirle dónde está el venv
  (lsp-pyright-venv-path . ".")
  (lsp-pyright-venv . ".venv")

  ;; Activar direnv para cargar env vars
  (eval . (direnv-update-environment))
  ))
