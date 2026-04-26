# https://docs.openwebui.com/getting-started/quick-start
helm repo add open-webui https://open-webui.github.io/helm-charts
helm repo update
helm install openwebui open-webui/open-webui --namespace openwebui --create-namespace

# fsh ➜ helm install openwebui open-webui/open-webui --namespace openwebui --create-namespace
# NAME: openwebui
# LAST DEPLOYED: Mon Apr 13 22:00:59 2026
# NAMESPACE: openwebui
# STATUS: deployed
# REVISION: 1
# DESCRIPTION: Install complete
# NOTES:
# 🎉 Welcome to Open WebUI!!
#  ██████╗ ██████╗ ███████╗███╗   ██╗    ██╗    ██╗███████╗██████╗ ██╗   ██╗██╗
# ██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ██║    ██║██╔════╝██╔══██╗██║   ██║██║
# ██║   ██║██████╔╝█████╗  ██╔██╗ ██║    ██║ █╗ ██║█████╗  ██████╔╝██║   ██║██║
# ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║    ██║███╗██║██╔══╝  ██╔══██╗██║   ██║██║
# ╚██████╔╝██║     ███████╗██║ ╚████║    ╚███╔███╔╝███████╗██████╔╝╚██████╔╝██║
#  ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝     ╚══╝╚══╝ ╚══════╝╚═════╝  ╚═════╝ ╚═╝

# v0.8.12 - building the best open-source AI user interface.
#  - Chart Version: v13.3.1
#  - Project URL 1: https://www.openwebui.com/
#  - Project URL 2: https://github.com/open-webui/open-webui
#  - Documentation: https://docs.openwebui.com/
#  - Chart URL: https://github.com/open-webui/helm-charts

# Open WebUI is a web-based user interface that works with Ollama, OpenAI, Claude 3, Gemini and more.
# This interface allows you to easily interact with local AI models.

# 1. Deployment Information:
#   - Chart Name: open-webui
#   - Release Name: openwebui
#   - Namespace: openwebui

# 2. Access the Application:
#   Access via ClusterIP service:

#     export LOCAL_PORT=8080
#     export POD_NAME=$(kubectl get pods -n openwebui -l "app.kubernetes.io/component=open-webui" -o jsonpath="{.items[0].metadata.name}")
#     export CONTAINER_PORT=$(kubectl get pod -n openwebui $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
#     kubectl -n openwebui port-forward $POD_NAME $LOCAL_PORT:$CONTAINER_PORT
#     echo "Visit http://127.0.0.1:$LOCAL_PORT to use your application"

#   Then, access the application at: http://127.0.0.1:$LOCAL_PORT or http://localhost:8080

# 3. Useful Commands:
#   - Check deployment status:
#       helm status openwebui -n openwebui

#   - Get detailed information:
#       helm get all openwebui -n openwebui

#   - View logs:
#       kubectl logs -f statefulset/openwebui-open-webui -n openwebui

# 4. Cleanup:
#   - Uninstall the deployment:
#       helm uninstall openwebui -n openwebui

# 5. Update Open WebUI:
#   - Refresh the chart repository:
#       helm repo update
#
#   - Upgrade the existing release using the current release values:
#       helm upgrade openwebui open-webui/open-webui \
#         --namespace openwebui \
#         --reuse-values
#
#   - Wait for the Open WebUI workload to finish rolling out:
#       kubectl rollout status statefulset/openwebui-open-webui -n openwebui
#
#   - Verify the running image:
#       kubectl get pod -n openwebui \
#         -l app.kubernetes.io/component=open-webui \
#         -o jsonpath='{.items[0].spec.containers[0].image}{"\n"}'
#
#   - Re-apply the NodePort service manifest if needed:
#       kubectl apply -f openwebui/kubectl-yaml/
