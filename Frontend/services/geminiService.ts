import { GoogleGenerativeAI } from "@google/generative-ai";

const apiKey = import.meta.env.VITE_GEMINI_API_KEY || process.env.GEMINI_API_KEY;
// const apiKey = "AIzaSyC4kL3ZkdeQJ7nhbrRmLvSM3Eg9hNKCvVU";

if (!apiKey) {
    console.warn("GEMINI_API_KEY environment variable not set. Gemini API calls will fail.");
}

const genAI = new GoogleGenerativeAI(apiKey || "dummy-key");

export const translateToMongoQuery = async (
    naturalLanguageQuery: string,
    schema: Record<string, 'string' | 'number' | 'boolean'>
): Promise<string> => {
    
    // Add validation for API key first
    if (!apiKey || apiKey === "dummy-key") {
        console.warn("No valid Gemini API key found, using simple fallback query");
        // Return a simple query as fallback
        return '[{"$limit": 10}]';
    }
    
    const prompt = `
        You are an expert data analyst who translates natural language questions into executable MongoDB Aggregation Pipeline queries.
        Your response MUST be ONLY the JSON for the MongoDB aggregation pipeline, represented as a string. Do not include any explanations, markdown formatting, or any text other than the JSON string itself.

        Dataset Schema:
        ${JSON.stringify(schema, null, 2)}

        User Question:
        "${naturalLanguageQuery}"

        Generate the MongoDB aggregation pipeline as a JSON string. For example:
        '[{"$match":{"gender":"female","employment_status":"employed"}},{"$group":{"_id":"$state","average_income":{"$avg":"$monthly_income"}}}]'
    `;

    try {
        const model = genAI.getGenerativeModel({ model: "gemini-pro" });
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const text = response.text().trim();
        
        // Clean up potential markdown code fences
        let cleanedText = text;
        if (cleanedText.startsWith('```json')) {
            cleanedText = cleanedText.substring(7);
        }
        if (cleanedText.endsWith('```')) {
            cleanedText = cleanedText.substring(0, cleanedText.length - 3);
        }
        
        // Basic validation to see if it's a valid JSON array
        try {
            JSON.parse(cleanedText);
            return cleanedText;
        } catch (e) {
            console.error("Gemini returned non-JSON response:", text);
            return '[{"$limit": 10}]'; // Fallback to simple query
        }

    } catch (error) {
        console.error("Error calling Gemini API:", error);
        return '[{"$limit": 10}]'; // Fallback to simple query
    }
};

export const testGeminiConnection = async (): Promise<boolean> => {
    if (!apiKey || apiKey === "dummy-key") {
        return false;
    }
    
    try {
        const model = genAI.getGenerativeModel({ model: "gemini-pro" });
        await model.generateContent("Hello");
        return true;
    } catch (error) {
        console.error("Gemini API test failed:", error);
        return false;
    }
};