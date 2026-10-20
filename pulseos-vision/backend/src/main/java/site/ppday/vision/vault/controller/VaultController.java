package site.ppday.vision.vault.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import site.ppday.vision.vault.dto.VaultBatchDeleteRequest;
import site.ppday.vision.vault.dto.VaultStatsResponse;
import site.ppday.vision.vault.service.VaultService;

import java.util.Map;

@RestController
@RequestMapping({"/api/vault", "/api/vision/vault"})
@CrossOrigin(origins = "*")
public class VaultController {

    private final VaultService vaultService;

    @Autowired
    public VaultController(VaultService vaultService) {
        this.vaultService = vaultService;
    }

    @GetMapping("/stats")
    public ResponseEntity<VaultStatsResponse> getVaultStats(@RequestParam(value = "drive", required = false, defaultValue = "local") String drive) {
        VaultStatsResponse stats = vaultService.getVaultStats(drive);
        return ResponseEntity.ok(stats);
    }

    @PostMapping("/batch-delete")
    public ResponseEntity<Map<String, Object>> batchDelete(@RequestBody VaultBatchDeleteRequest request) {
        Map<String, Object> res = vaultService.batchDeleteFiles(request.getFileIds());
        return ResponseEntity.ok(res);
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
            "status", "UP",
            "service", "PulseOS-Vault-Spring-Boot",
            "timestamp", System.currentTimeMillis()
        ));
    }
}
