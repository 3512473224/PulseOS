package site.ppday.vision.controller;

import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.Arrays;

@RestController
@RequestMapping("/api/vision")
@CrossOrigin(origins = "*") // Allow all for demo purposes, restrict in production
public class VisionController {

    @GetMapping("/stats")
    public Map<String, Object> getStats() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("status", "ACTIVE");
        stats.put("latency", Math.random() * 50 + 10);
        stats.put("particles", 15000);
        stats.put("system_load", Math.random() * 100);
        
        List<String> coreModules = Arrays.asList(
            "Quantum Engine", 
            "Neural Interface", 
            "Data Stream Processor"
        );
        stats.put("modules", coreModules);

        return stats;
    }
    
    @GetMapping("/system")
    public Map<String, String> getSystemInfo() {
        Map<String, String> info = new HashMap<>();
        info.put("os", "PulseOS Vision Core");
        info.put("version", "v3.0.0-alpha");
        info.put("architecture", "Global Node Network");
        return info;
    }
}
