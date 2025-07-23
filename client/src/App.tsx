import React, { useState } from "react";
import { Box, Button, Card, CardContent, Typography, Grid, Alert, Paper, IconButton, Chip } from "@mui/material";
import {
	CloudUpload as CloudUploadIcon,
	Image as ImageIcon,
	PictureAsPdf as PdfIcon,
	Code as JsonIcon,
	TextFields as TextIcon,
	Delete as DeleteIcon,
} from "@mui/icons-material";
import "./App.css";

interface FileState {
	images: File[];
	pdf: File[];
	json: File[];
	txt: File[];
}

function App() {
	const [files, setFiles] = useState<FileState>({
		images: [],
		pdf: [],
		json: [],
		txt: [],
	});
	const [error, setError] = useState<string>("");

	const handleFileChange = (fileType: keyof FileState, selectedFiles: FileList | null) => {
		if (selectedFiles) {
			setFiles((prev) => ({
				...prev,
				[fileType]: Array.from(selectedFiles),
			}));
			setError("");
		}
	};

	const removeFile = (fileType: keyof FileState, index: number) => {
		setFiles((prev) => ({
			...prev,
			[fileType]: prev[fileType].filter((_, i) => i !== index),
		}));
	};

	const handleSubmit = async () => {
		const hasFiles = Object.values(files).some((fileArray) => fileArray.length > 0);

		if (!hasFiles) {
			setError("Please select at least one file before submitting.");
			return;
		}

		const formData = new FormData();

		// Append all files to FormData
		(Object.keys(files) as (keyof FileState)[]).forEach((fileType) => {
			files[fileType].forEach((file, index) => {
				// We'll prefix field names with the file type
				formData.append(`${fileType}`, file);
			});
		});

		try {
			const response = await fetch("http://localhost:5000/upload", {
				method: "POST",
				body: formData,
			});

			const result = await response.json();
			if (response.ok) {
				alert(`Files uploaded successfully: ${JSON.stringify(result.uploaded_files, null, 2)}`);
				setFiles({ images: [], pdf: [], json: [], txt: [] }); // Reset files after upload
				setError("");
			} else {
				setError(result.error || "Upload failed");
			}
		} catch (err: any) {
			console.error(err);
			setError(err.message || "Upload error occurred");
		}
	};

	const FileSelector = ({
		type,
		accept,
		icon,
		label,
		multiple = false,
	}: {
		type: keyof FileState;
		accept: string;
		icon: React.ReactNode;
		label: string;
		multiple?: boolean;
	}) => (
		<Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
			<CardContent sx={{ flexGrow: 1 }}>
				<Box display="flex" alignItems="center" mb={2}>
					{icon}
					<Typography variant="h6" sx={{ ml: 1 }}>
						{label}
					</Typography>
				</Box>

				<Button variant="outlined" component="label" fullWidth startIcon={<CloudUploadIcon />} sx={{ mb: 2 }}>
					Choose Files
					<input
						type="file"
						hidden
						accept={accept}
						multiple={multiple}
						onChange={(e) => handleFileChange(type, e.target.files)}
					/>
				</Button>

				{files[type].length > 0 && (
					<Box>
						<Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
							Selected files:
						</Typography>
						{files[type].map((file, index) => (
							<Chip
								key={index}
								label={file.name}
								onDelete={() => removeFile(type, index)}
								deleteIcon={<DeleteIcon />}
								size="small"
								sx={{ mr: 1, mb: 1 }}
							/>
						))}
					</Box>
				)}
			</CardContent>
		</Card>
	);

	return (
		<Box sx={{ minHeight: "100vh", bgcolor: "grey.50", py: 4 }}>
			<Box sx={{ maxWidth: 1200, mx: "auto", px: 3 }}>
				<Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
					<Typography variant="h4" component="h1" gutterBottom align="center" sx={{ mb: 4 }}>
						File Upload Center
					</Typography>

					{error && (
						<Alert severity="error" sx={{ mb: 3 }}>
							{error}
						</Alert>
					)}

					<Grid container spacing={3} sx={{ mb: 4 }}>
						<Grid item xs={12} sm={6} md={3}>
							<FileSelector
								type="images"
								accept="image/*"
								icon={<ImageIcon color="primary" />}
								label="Images"
								multiple
							/>
						</Grid>

						<Grid item xs={12} sm={6} md={3}>
							<FileSelector
								type="pdf"
								accept=".pdf"
								icon={<PdfIcon color="error" />}
								label="PDF Files"
								multiple
							/>
						</Grid>

						<Grid item xs={12} sm={6} md={3}>
							<FileSelector
								type="json"
								accept=".json"
								icon={<JsonIcon color="success" />}
								label="JSON Files"
								multiple
							/>
						</Grid>

						<Grid item xs={12} sm={6} md={3}>
							<FileSelector
								type="txt"
								accept=".txt"
								icon={<TextIcon color="warning" />}
								label="Text Files"
								multiple
							/>
						</Grid>
					</Grid>

					<Box display="flex" justifyContent="center">
						<Button
							variant="contained"
							size="large"
							onClick={handleSubmit}
							startIcon={<CloudUploadIcon />}
							sx={{ px: 4, py: 1.5 }}
						>
							Submit Files
						</Button>
					</Box>
				</Paper>
			</Box>
		</Box>
	);
}

export default App;
