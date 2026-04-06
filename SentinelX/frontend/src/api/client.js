export const API_BASE_URL = "http://localhost:8000/api/v1";

export const fetchWithAuth = async (endpoint, options = {}) => {
    const token = localStorage.getItem("access_token");
    
    // Set headers
    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };
    
    // Inject JWT token if it exists
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
        });

        // Handle 401 Unauthorized globally
        if (response.status === 401) {
            console.error("Authentication expired or invalid.");
            localStorage.removeItem("access_token");
            window.location.href = "/login"; // Force redirect to login
            return null;
        }

        // Parse JSON response
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.detail || "API request failed");
        }

        return data;
    } catch (error) {
        console.error(`API Error on ${endpoint}:`, error);
        throw error;
    }
};

export const login = async (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: params
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Login failed");
    }

    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    return data;
};

export const logout = () => {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
};
