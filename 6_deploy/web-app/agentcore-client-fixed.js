class FixedAgentCoreClient {
  constructor() {
    this.agentRuntimeArn = null;
    this.isInitialized = false;
    this.credentials = null;

    this.LOCALSTORAGE_KEY = 'chatbot_session_id';
    this.sessionId = this.#initSession();
  }

  // === Session handling ===
  #safeLocalStorageGet(key) {
    try { return window.localStorage.getItem(key); } catch { return null; }
  }
  #safeLocalStorageSet(key, val) {
    try { window.localStorage.setItem(key, val); } catch { /* ignore */ }
  }
  #generateSessionId() {
    // Generate a UUID v4 (36 characters including hyphens) and prefix to ensure >=33 length always
    const uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
    return `session-${uuid}`; // total length 43 with prefix
  }
  #initSession() {
    const existing = this.#safeLocalStorageGet(this.LOCALSTORAGE_KEY);
    if (existing && typeof existing === 'string' && existing.trim() && existing.length >= 33) return existing;
    const fresh = this.#generateSessionId();
    this.#safeLocalStorageSet(this.LOCALSTORAGE_KEY, fresh);
    return fresh;
  }

  getSessionId() { return this.sessionId; }
  setSessionId(newId) {
    if (!newId || typeof newId !== 'string' || newId.length < 33) throw new Error('Invalid session id');
    this.sessionId = newId;
    this.#safeLocalStorageSet(this.LOCALSTORAGE_KEY, newId);
  }
  resetSession() {
    const fresh = this.#generateSessionId();
    this.setSessionId(fresh);
    console.log('Session reset. New session ID:', fresh);
    return fresh;
  }

  // === Initialization ===
  async initialize() {
    if (this.isInitialized) return; // idempotent
    try {
      console.log('🔧 Initializing Fixed AgentCore client...');

      // 1) Load AgentCore configuration
      await this.#loadAgentCoreConfig();
      console.log('✅ AgentCore configuration loaded');

      // 2) Fetch AWS credentials via your Cognito wrapper
      console.log('Step 2: Getting AWS credentials...');
      this.credentials = await window.CognitoAuth.getCurrentAWSCredentials();
      console.log('✅ AWS credentials obtained');

      // 3) Configure global AWS SDK
      AWS.config.update({
        region: 'us-west-2',
        accessKeyId: this.credentials.accessKeyId,
        secretAccessKey: this.credentials.secretAccessKey,
        sessionToken: this.credentials.sessionToken,
      });

      this.isInitialized = true;
      console.log('✅ Fixed AgentCore client initialized successfully');
      console.log('Agent Runtime ARN:', this.agentRuntimeArn);
      console.log('Session ID:', this.sessionId);
    } catch (err) {
      console.error('❌ Failed to initialize Fixed AgentCore client:', err);
      throw new Error(`AgentCore initialization failed: ${err.message}`);
    }
  }

  async #loadAgentCoreConfig() {
    try {
      const resp = await fetch('agentcore-config.json', { cache: 'no-store' });
      const cfg = await resp.json();
      if (!cfg || !cfg.agentRuntimeArn) throw new Error('agentRuntimeArn missing in agentcore-config.json');
      this.agentRuntimeArn = cfg.agentRuntimeArn;
    } catch (e) {
      console.error('Failed to load AgentCore configuration:', e);
      throw e;
    }
  }

  // === Messaging ===
  async sendMessage(message) {
    if (!this.isInitialized) await this.initialize();

    // --- build lightweight context from storage ---
    const userId = sessionStorage.getItem('username') || 'anonymous';
    let store = null;
    try { store = JSON.parse(sessionStorage.getItem('selectedStore') || 'null'); } catch {}
    const storeBits = store ? `; storeId=${store.store_id}; storeName="${store.name}"; storeCity="${store.city}"` : '';
    const ctxBlock = `[[CTX]] userId=${userId}${storeBits} [[/CTX]]\n`;
    const prompt = ctxBlock + message;
    // ------------------------------------------------

    const payload = JSON.stringify({ prompt });
    const baseUrl = 'https://bedrock-agentcore.us-west-2.amazonaws.com';
    const runtimeArnEnc = encodeURIComponent(this.agentRuntimeArn);
    const session = encodeURIComponent(this.sessionId);
    const url = `${baseUrl}/runtimes/${runtimeArnEnc}/invocations?qualifier=DEFAULT&runtimeSessionId=${session}`;

    const { host } = new URL(url);
    const awsReq = new AWS.HttpRequest(url, 'us-west-2');
    awsReq.method = 'POST';
    awsReq.headers = {
      'host': host,
      'content-type': 'application/json',
      'accept': 'application/json',
      'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': this.sessionId,
    };
    awsReq.body = payload;

    const signer = new AWS.Signers.V4(awsReq, 'bedrock-agentcore');
    signer.addAuthorization(this.credentials, new Date());

    const resp = await fetch(url, { method: 'POST', headers: awsReq.headers, body: payload });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${await resp.text()}`);
    const text = await resp.text();
    try { const parsed = JSON.parse(text); return typeof parsed === 'string' ? { message: parsed } : parsed; }
    catch { return { message: text || 'Empty response from agent' }; }
  }


  // === Status ===
  isReady() { return this.isInitialized && !!this.credentials; }
}

// Create a global singleton so the same session is reused across your app
window.fixedAgentCoreClient = new FixedAgentCoreClient();
