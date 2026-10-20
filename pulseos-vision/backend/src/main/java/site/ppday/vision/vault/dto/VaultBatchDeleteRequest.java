package site.ppday.vision.vault.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class VaultBatchDeleteRequest {
    @JsonProperty("file_ids")
    private List<String> fileIds;

    public List<String> getFileIds() { return fileIds; }
    public void setFileIds(List<String> fileIds) { this.fileIds = fileIds; }
}
