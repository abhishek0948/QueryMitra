import { GoogleGenerativeAI } from "@google/generative-ai";

// For frontend, we'll let the backend handle Gemini API calls for security
// This maintains the existing interface but delegates to backend
const apiKey = import.meta.env.VITE_GEMINI_API_KEY;

if (!apiKey) {
    console.warn("GEMINI_API_KEY environment variable not set. Using backend for NL translation.");
}

const genAI = apiKey ? new GoogleGenerativeAI(apiKey) : null;

export const translateToMongoQuery = async (
    naturalLanguageQuery: string,
    schema: Record<string, 'string' | 'number' | 'boolean'>
): Promise<string> => {
    
    // If no frontend API key, let backend handle the translation
    if (!apiKey || apiKey === "dummy-key" || !genAI) {
        console.log("Delegating NL translation to backend");
        // Return the original query - backend will handle translation
        return naturalLanguageQuery;
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
        const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const text = response.text().trim();
        
        // Clean up potential markdown code fences
        let cleanedText = text;
        if (cleanedText.startsWith('```json')) {
            cleanedText = cleanedText.substring(7);
        }
        if (cleanedText.startsWith('```')) {
            cleanedText = cleanedText.substring(3);
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
    if (!apiKey || apiKey === "dummy-key" || !genAI) {
        return false;
    }
    
    try {
        const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });
        await model.generateContent("Hello");
        return true;
    } catch (error) {
        console.error("Gemini API test failed:", error);
        return false;
    }
};