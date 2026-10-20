package site.ppday.vision.vault.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

public class VaultStatsResponse {
    private boolean success = true;
    
    @JsonProperty("current_drive")
    private String currentDrive;
    
    @JsonProperty("active_drive")
    private DriveStatsDTO activeDrive;
    
    private Map<String, DriveStatsDTO> drives;
    
    @JsonProperty("vault_file_count")
    private int vaultFileCount;
    
    @JsonProperty("vault_used_bytes")
    private long vaultUsedBytes;
    
    @JsonProperty("vault_used_formatted")
    private String vaultUsedFormatted;
    
    @JsonProperty("disk_total_bytes")
    private long diskTotalBytes;
    
    @JsonProperty("disk_free_bytes")
    private long diskFreeBytes;
    
    @JsonProperty("disk_free_formatted")
    private String diskFreeFormatted;
    
    @JsonProperty("disk_used_percent")
    private double diskUsedPercent;

    public boolean isSuccess() { return success; }
    public void setSuccess(boolean success) { this.success = success; }

    public String getCurrentDrive() { return currentDrive; }
    public void setCurrentDrive(String currentDrive) { this.currentDrive = currentDrive; }

    public DriveStatsDTO getActiveDrive() { return activeDrive; }
    public void setActiveDrive(DriveStatsDTO activeDrive) { this.activeDrive = activeDrive; }

    public Map<String, DriveStatsDTO> getDrives() { return drives; }
    public void setDrives(Map<String, DriveStatsDTO> drives) { this.drives = drives; }

    public int getVaultFileCount() { return vaultFileCount; }
    public void setVaultFileCount(int vaultFileCount) { this.vaultFileCount = vaultFileCount; }

    public long getVaultUsedBytes() { return vaultUsedBytes; }
    public void setVaultUsedBytes(long vaultUsedBytes) { this.vaultUsedBytes = vaultUsedBytes; }

    public String getVaultUsedFormatted() { return vaultUsedFormatted; }
    public void setVaultUsedFormatted(String vaultUsedFormatted) { this.vaultUsedFormatted = vaultUsedFormatted; }

    public long getDiskTotalBytes() { return diskTotalBytes; }
    public void setDiskTotalBytes(long diskTotalBytes) { this.diskTotalBytes = diskTotalBytes; }

    public long getDiskFreeBytes() { return diskFreeBytes; }
    public void setDiskFreeBytes(long diskFreeBytes) { this.diskFreeBytes = diskFreeBytes; }

    public String getDiskFreeFormatted() { return diskFreeFormatted; }
    public void setDiskFreeFormatted(String diskFreeFormatted) { this.diskFreeFormatted = diskFreeFormatted; }

    public double getDiskUsedPercent() { return diskUsedPercent; }
    public void setDiskUsedPercent(double diskUsedPercent) { this.diskUsedPercent = diskUsedPercent; }
}
