function app() {
    return {
        isDark: false,
        isLoggedIn: false, // DEFAULT FALSE
        isLoggingIn: false,
        loginError: null,
        loginForm: {
            email: '',
            password: ''
        },
        isLoading: false,
        userEmail: '',
        stats: {
            processedCount: 0,
            totalValue: 0
        },
        queue: [],
        processingFile: null,
        history: [],
        csvResults: [],

        // CONFIGURATION
        // Point this to your Python API Container's Public URL
        API_BASE_URL: 'https://invoice-api.huwanbisente.online',

        init() {
            // 1. Dark Mode
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                this.isDark = true;
            }

            // 2. CHECK LOCAL STORAGE FOR SESSION
            const savedEmail = localStorage.getItem('APIR_UserEmail');
            if (savedEmail) {
                this.userEmail = savedEmail;
                this.isLoggedIn = true;
                this.loadUserData(); // Restore data
            }
        },

        toggleTheme() {
            this.isDark = !this.isDark;
        },

        // LOGIN LOGIC
        async login() {
            this.isLoggingIn = true;
            this.loginError = null;

            try {
                const res = await fetch(`${this.API_BASE_URL}/api/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.loginForm)
                });
                const data = await res.json();

                if (data.success) {
                    this.isLoggingIn = false;
                    this.isLoggedIn = true;
                    this.userEmail = data.email;
                    this.loginForm.password = '';
                    localStorage.setItem('APIR_UserEmail', this.userEmail);
                    this.loadUserData();
                } else {
                    this.isLoggingIn = false;
                    this.loginError = data.error;
                }
            } catch (err) {
                this.isLoggingIn = false;
                this.loginError = "Connection Error: " + err.toString();
            }
        },

        logout() {
            localStorage.removeItem('APIR_UserEmail');
            this.isLoggedIn = false;
            this.userEmail = '';
            this.history = [];
            this.csvResults = [];
            this.stats = { processedCount: 0, totalValue: 0 };
        },

        async loadUserData() {
            if (!this.userEmail) return;

            try {
                const res = await fetch(`${this.API_BASE_URL}/api/history?email=${encodeURIComponent(this.userEmail)}`);
                const data = await res.json();

                if (data.success && data.history) {
                    // Clear current to prevent dupes
                    this.history = [];
                    this.csvResults = [];
                    this.stats = { processedCount: 0, totalValue: 0 };

                    // Reverse to show newest first
                    data.history.forEach(item => {
                        this.addToHistory(item);
                        this.addToCSVTable(item);
                    });

                    if (data.history.length > 0) {
                        Swal.fire({
                            toast: true,
                            position: 'top-end',
                            icon: 'success',
                            title: `Restored ${data.history.length} invoices`,
                            timer: 2000,
                            showConfirmButton: false
                        });
                    }
                }
            } catch (e) {
                console.error("Failed to load history", e);
            }
        },

        // Actions
        async clearData() {
            try {
                const res = await fetch(`${this.API_BASE_URL}/api/clear`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: this.userEmail })
                });
                const data = await res.json();

                if (data.success) {
                    this.history = [];
                    this.csvResults = [];
                    this.stats.processedCount = 0;
                    this.stats.totalValue = 0;
                    Swal.fire('Deleted!', 'Your workspace has been reset.', 'success');
                }
            } catch (e) {
                this.handleError("Could not clear workspace");
            }
        },
        downloadCSV() {
            if (this.csvResults.length === 0) return;
            const headers = Object.keys(this.csvResults[0]).join(",");
            const rows = this.csvResults.map(row =>
                Object.values(row).map(val => `"${val}"`).join(",")
            );
            const csvContent = [headers, ...rows].join("\n");
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);
            link.setAttribute("href", url);
            link.setAttribute("download", `invoices_export_${new Date().toISOString().slice(0, 10)}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        handleFileSelect(e) {
            const files = e.target.files;
            if (files.length > 0) {
                Array.from(files).forEach(file => {
                    this.queue.push(file);
                });
                e.target.value = '';
            }
        },

        startProcessing() {
            if (!this.isLoading && this.queue.length > 0) {
                this.processQueue();
            }
        },

        processQueue() {
            if (this.queue.length === 0) {
                this.isLoading = false;
                this.processingFile = null;
                return;
            }

            this.isLoading = true;
            const file = this.queue[0];
            this.processingFile = file.name;

            // USE FETCH INSTEAD OF FILEREADER+GAS
            const formData = new FormData();
            formData.append('file', file);
            formData.append('email', this.userEmail); // Include Email for DB saving

            // IMPORTANT: Adjust this URL if your API is on a different port/host
            const API_URL = `${this.API_BASE_URL}/api/parse`;

            fetch(API_URL, {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(res => {
                    if (res.success) {
                        const invoices = Array.isArray(res.data) ? res.data : [res.data];
                        invoices.forEach(invoice => {
                            this.addToHistory(invoice);
                            this.addToCSVTable(invoice);
                        });
                        this.queue.shift();
                        this.processQueue();
                    } else {
                        this.handleError(res.error || "Unknown Error");
                    }
                })
                .catch(err => {
                    this.handleError(err.toString());
                });
        },

        handleError(msg) {
            Swal.fire({
                toast: true,
                position: 'top-end',
                icon: 'error',
                title: 'Error Processing ' + (this.processingFile || 'File'),
                text: msg,
                timer: 3000,
                showConfirmButton: false,
                background: this.isDark ? '#1e293b' : '#fff',
                color: this.isDark ? '#fff' : '#000'
            });
            // Move to next even on error
            this.queue.shift();
            this.processQueue();
        },

        addToHistory(data) {
            const total = data.total_amount || 0;
            this.history.unshift({
                id: Date.now() + Math.random(),
                time: new Date(data.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                vendor: data.vendor_name || 'Unknown',
                total: new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(total),
                itemsCount: (data.line_items || []).length
            });
            this.stats.processedCount++;
            this.stats.totalValue += Number(total);
        },

        addToCSVTable(data) {
            const common = {
                vendor: data.vendor_name,
                inv_num: data.invoice_number,
                date: data.invoice_date,
                due: data.due_date,
                tax: data.tax_amount,
                total: data.total_amount,
                curr: data.currency
            };
            if (data.line_items && data.line_items.length > 0) {
                data.line_items.forEach(item => {
                    this.csvResults.push({ ...common, ...item });
                });
            } else {
                this.csvResults.push({ ...common, description: '', quantity: '', unit_price: '', amount: '' });
            }
        }
    }
}
