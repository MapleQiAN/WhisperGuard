package main

import (
	"bytes"
	"encoding/json"
	"log"
	"net/http"
	"os"
)

type AnalyzeRequest struct {
	Text  string `json:"text"`
	Model string `json:"model"`
}

type AnalyzeResponse struct {
	SensitiveWords []string `json:"sensitive_words"`
	RiskLevel      string   `json:"risk_level"`
	RiskReason     string   `json:"risk_reason"`
	Rewrite        []string `json:"rewrite"`
}

func enableCORS(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next(w, r)
	}
}

func main() {
	http.HandleFunc("/analyze", enableCORS(handleAnalyze))
	http.HandleFunc("/health", enableCORS(handleHealth))

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("服务启动在端口 %s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
}

func handleAnalyze(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "只支持 POST 请求", http.StatusMethodNotAllowed)
		return
	}

	var req AnalyzeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "无效的请求体", http.StatusBadRequest)
		return
	}

	// 调用Python服务
	pyServiceURL := os.Getenv("PY_SERVICE_URL")
	if pyServiceURL == "" {
		pyServiceURL = "http://localhost:8000"
	}

	pyReq, err := json.Marshal(req)
	if err != nil {
		http.Error(w, "请求处理失败", http.StatusInternalServerError)
		return
	}

	resp, err := http.Post(pyServiceURL+"/analyze", "application/json", bytes.NewBuffer(pyReq))
	if err != nil {
		http.Error(w, "Python服务调用失败", http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	var result AnalyzeResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		http.Error(w, "响应解析失败", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}
