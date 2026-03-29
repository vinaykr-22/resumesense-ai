import api from '../lib/api';

/**
 * Service for V2 Analysis features
 */
const analysisService = {
  /**
   * Performs an ad-hoc analysis of a resume against a raw JD text
   * @param {string} resumeId - The ID of the resume
   * @param {string} jdText - The raw text of the job description
   */
  async analyzeWithJD(resumeId, jdText) {
    // This calls the suggestions endpoint which we updated in the backend
    // to handle long target_role inputs as JD text.
    return api.post('/resume/suggestions', {
      resume_id: resumeId,
      target_role: jdText
    });
  },

  /**
   * Fetches the full V2 analysis result from Redis
   * @param {string} resumeId 
   */
  async getV2Results(resumeId) {
    // We can use the existing status endpoint which returns the full result once completed
    const response = await api.get(`/resume/status/${resumeId}`);
    return response.data;
  },

  /**
   * Compares two resume versions
   */
  async compareVersions(v1, v2) {
    return api.get(`/resume/compare?v1=${v1}&v2=${v2}`);
  }
};

export default analysisService;
