package site.ppday.vision.vault.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

public class DriveStatsDTO {
    private String key;
    private String name;
    private String icon;
    
    @JsonProperty("icon_color")
    private String iconColor;
    
    private String path;
    
    @JsonProperty("file_count")
    private int fileCount;
    
    @JsonProperty("file_count_label")
    private String fileCountLabel;
    
    @JsonProperty("file_count_sub")
    private String fileCountSub;
    
    @JsonProperty("used_bytes")
    private long usedBytes;
    
    @JsonProperty("used_formatted")
    private String usedFormatted;
    
    @JsonProperty("used_label")
    private String usedLabel;
    
    @JsonProperty("used_sub")
    private String usedSub;
    
    @JsonProperty("free_bytes")
    private long freeBytes;
    
    @JsonProperty("free_formatted")
    private String freeFormatted;
    
    @JsonProperty("free_label")
    private String freeLabel;
    
    @JsonProperty("free_sub")
    private String freeSub;
    
    @JsonProperty("total_bytes")
    private long totalBytes;
    
    @JsonProperty("total_formatted")
    private String totalFormatted;
    
    @JsonProperty("used_percent")
    private double usedPercent;
    
    @JsonProperty("max_file_size")
    private String maxFileSize;
    
    @JsonProperty("max_file_size_sub")
    private String maxFileSizeSub;
    
    @JsonProperty("sync_status")
    private String syncStatus;
    
    @JsonProperty("sync_sub")
    private String syncSub;

    // Getters and Setters
    public String getKey() { return key; }
    public void setKey(String key) { this.key = key; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getIcon() { return icon; }
    public void setIcon(String icon) { this.icon = icon; }

    public String getIconColor() { return iconColor; }
    public void setIconColor(String iconColor) { this.iconColor = iconColor; }

    public String getPath() { return path; }
    public void setPath(String path) { this.path = path; }

    public int getFileCount() { return fileCount; }
    public void setFileCount(int fileCount) { this.fileCount = fileCount; }

    public String getFileCountLabel() { return fileCountLabel; }
    public void setFileCountLabel(String fileCountLabel) { this.fileCountLabel = fileCountLabel; }

    public String getFileCountSub() { return fileCountSub; }
    public void setFileCountSub(String fileCountSub) { this.fileCountSub = fileCountSub; }

    public long getUsedBytes() { return usedBytes; }
    public void setUsedBytes(long usedBytes) { this.usedBytes = usedBytes; }

    public String getUsedFormatted() { return usedFormatted; }
    public void setUsedFormatted(String usedFormatted) { this.usedFormatted = usedFormatted; }

    public String getUsedLabel() { return usedLabel; }
    public void setUsedLabel(String usedLabel) { this.usedLabel = usedLabel; }

    public String getUsedSub() { return usedSub; }
    public void setUsedSub(String usedSub) { this.usedSub = usedSub; }

    public long getFreeBytes() { return freeBytes; }
    public void setFreeBytes(long freeBytes) { this.freeBytes = freeBytes; }

    public String getFreeFormatted() { return freeFormatted; }
    public void setFreeFormatted(String freeFormatted) { this.freeFormatted = freeFormatted; }

    public String getFreeLabel() { return freeLabel; }
    public void setFreeLabel(String freeLabel) { this.freeLabel = freeLabel; }

    public String getFreeSub() { return freeSub; }
    public void setFreeSub(String freeSub) { this.freeSub = freeSub; }

    public long getTotalBytes() { return totalBytes; }
    public void setTotalBytes(long totalBytes) { this.totalBytes = totalBytes; }

    public String getTotalFormatted() { return totalFormatted; }
    public void setTotalFormatted(String totalFormatted) { this.totalFormatted = totalFormatted; }

    public double getUsedPercent() { return usedPercent; }
    public void setUsedPercent(double usedPercent) { this.usedPercent = usedPercent; }

    public String getMaxFileSize() { return maxFileSize; }
    public void setMaxFileSize(String maxFileSize) { this.maxFileSize = maxFileSize; }

    public String getMaxFileSizeSub() { return maxFileSizeSub; }
    public void setMaxFileSizeSub(String maxFileSizeSub) { this.maxFileSizeSub = maxFileSizeSub; }

    public String getSyncStatus() { return syncStatus; }
    public void setSyncStatus(String syncStatus) { this.syncStatus = syncStatus; }

    public String getSyncSub() { return syncSub; }
    public void setSyncSub(String syncSub) { this.syncSub = syncSub; }
}
