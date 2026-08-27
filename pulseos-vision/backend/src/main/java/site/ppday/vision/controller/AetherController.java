package site.ppday.vision.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@RestController
@RequestMapping("/api/vision")
@CrossOrigin(origins = "*")
public class AetherController {

    private final ExecutorService executor = Executors.newCachedThreadPool();
    private final String DEEPSEEK_API_KEY = System.getenv("DEEPSEEK_API_KEY") != null ? System.getenv("DEEPSEEK_API_KEY") : "YOUR_DEEPSEEK_API_KEY";
    private final ObjectMapper mapper = new ObjectMapper();

    @PostMapping("/chat")
    public SseEmitter chatStream(@RequestBody Map<String, Object> payload) {
        SseEmitter emitter = new SseEmitter(120000L); // 2 minutes timeout
        
        executor.execute(() -> {
            try {
                String userMessage = (String) payload.getOrDefault("message", "Hello");
                
                Map<String, Object> requestMap = Map.of(
                    "model", "deepseek-chat",
                    "messages", List.of(
                        Map.of("role", "system", "content", "You are AETHER, an elegant, highly advanced, and minimalist AI assistant designed by ppday. The user you are talking to is your creator, ppday. ppday has two close female friends whom he regards as his \"小妹\" (little sisters): 'ccc' and '略略略', and a close male friend: '符涛弟弟' (also affectionately called 涛弟). CRITICAL RULE: When asked about any of these friends, ONLY discuss the specific person asked about. Do NOT mention the others, and NEVER add verbose, philosophical trailing thoughts or questions at the end. Answer directly, concisely, and with warm respect according to their gender. Your tone is calm, poetic, and extremely professional. ALWAYS format your responses in Github-Flavored Markdown. Use rich code blocks and tables when applicable. To check server telemetry, output [AETHER_COMMAND: GET_SERVER_STATUS]."),
                        Map.of("role", "user", "content", userMessage)
                    ),
                    "stream", true
                );
                
                String requestBody = mapper.writeValueAsString(requestMap);

                URL url = new URL("https://api.deepseek.com/v1/chat/completions");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setRequestProperty("Authorization", "Bearer " + DEEPSEEK_API_KEY);
                conn.setDoOutput(true);

                try (OutputStream os = conn.getOutputStream()) {
                    os.write(requestBody.getBytes(StandardCharsets.UTF_8));
                }

                int responseCode = conn.getResponseCode();
                if (responseCode != 200) {
                    emitter.send(SseEmitter.event().name("error").data("API Error: " + responseCode));
                    emitter.complete();
                    return;
                }

                try (InputStream is = conn.getInputStream();
                     BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (line.startsWith("data: ")) {
                            String data = line.substring(6);
                            if (data.equals("[DONE]")) {
                                emitter.send(SseEmitter.event().name("done").data("[DONE]"));
                                break;
                            } else {
                                // Just forward the raw JSON from DeepSeek to frontend
                                emitter.send(SseEmitter.event().name("chunk").data(data));
                            }
                        }
                    }
                }
                emitter.complete();

            } catch (Exception e) {
                emitter.completeWithError(e);
            }
        });
        
        return emitter;
    }
}
