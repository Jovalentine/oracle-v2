import os
import cv2
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_case_pdf(case_data, upload_dir, report_dir):
    """Generates a professional PDF report, handling both Images and Videos."""
    case_id = case_data["case_id"]
    case_type = case_data.get("type", "image")
    pdf_filename = f"Oracle_Forensic_Report_{case_id}.pdf"
    pdf_path = os.path.join(report_dir, pdf_filename)
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#0284c7"), spaceAfter=10)
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=10, textColor=colors.gray, spaceAfter=20)
    section_style = ParagraphStyle('SectionStyle', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor("#0f172a"), spaceBefore=15, spaceAfter=10)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=11, spaceAfter=10, leading=15)
    
    elements = []
    ai_data = case_data.get("analysis", {})

    # 1. Header
    elements.append(Paragraph("ORACLE FORENSIC SYSTEM", title_style))
    date_str = case_data["created_at"].strftime('%Y-%m-%d %H:%M:%S')
    elements.append(Paragraph(f"Official AI Reconstruction Dossier | Case #{case_id} | Type: {case_type.upper()} | Date: {date_str}", sub_style))
    
    # 2. Evidence Image / Video Thumbnail
    file_path = os.path.join(upload_dir, case_data["filename"])
    thumb_path = None

    if os.path.exists(file_path):
        elements.append(Paragraph("Primary Scene Evidence", section_style))
        
        if case_type == "video":
            # Extract a thumbnail frame from the video using OpenCV
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            if ret:
                thumb_path = os.path.join(report_dir, f"temp_thumb_{case_id}.jpg")
                cv2.imwrite(thumb_path, frame)
                img = RLImage(thumb_path, width=450, height=250, kind='proportional')
                elements.append(img)
            cap.release()
            elements.append(Paragraph("<i>(Video Thumbnail - See digital dossier for full playback)</i>", sub_style))
        else:
            # Standard Image
            img = RLImage(file_path, width=450, height=300, kind='proportional')
            elements.append(img)
            
        elements.append(Spacer(1, 15))

    # 3. Telemetry Table
    elements.append(Paragraph("Scene Telemetry", section_style))
    telemetry_data = [
        ["Collision Vector", ai_data.get("collision_type", "N/A")],
        ["Severity Score", f"{ai_data.get('severity_score', 'N/A')}/100"],
        ["Pedestrians Detected", str(ai_data.get("pedestrians_detected", False))],
        ["License Plates", ", ".join(ai_data.get("license_plates_detected", ["None"]))]
    ]
    
    # Add video metadata if present
    if case_type == "video" and "video_meta" in ai_data:
        telemetry_data.append(["Frames Analyzed", str(ai_data["video_meta"].get("frames_analyzed", "N/A"))])
        telemetry_data.append(["Source FPS", str(ai_data["video_meta"].get("fps", "N/A"))])

    t_table = Table(telemetry_data, colWidths=[150, 300])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f0f4f8")),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#0f172a")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
    ]))
    elements.append(t_table)

    # 4. Video Timeline (Only added if it's a video case)
    if case_type == "video" and "timeline" in ai_data:
        elements.append(Paragraph("Chronological Event Timeline", section_style))
        timeline_data = [["Time (sec)", "Event Detected"]]
        for event in ai_data["timeline"]:
            timeline_data.append([
                f"T+{event.get('timestamp_sec', '0')}s",
                Paragraph(event.get('event', ''), body_style)
            ])
            
        time_table = Table(timeline_data, colWidths=[80, 380])
        time_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#8b5cf6")), # Purple header for video
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(time_table)

    # 5. Fault Allocation Table
    elements.append(Paragraph("Fault Allocation", section_style))
    fault_data = [["Vehicle Type", "Fault %", "AI Reasoning"]]
    for vehicle in ai_data.get("vehicles_involved", []):
        fault_data.append([
            vehicle.get("type", "Unknown").capitalize(),
            f"{vehicle.get('fault_percentage', 0)}%",
            Paragraph(vehicle.get("reasoning", ""), body_style)
        ])
    
    f_table = Table(fault_data, colWidths=[100, 60, 340])
    f_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0284c7")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(f_table)

    # 6. Narrative
    elements.append(Paragraph("Investigative Narrative", section_style))
    narrative_text = ai_data.get("investigative_narrative", "").replace('\n', '<br/>')
    elements.append(Paragraph(narrative_text, body_style))

    # Generate the PDF
    doc.build(elements)
    
    # Cleanup: Delete the temporary video thumbnail so it doesn't take up space
    if thumb_path and os.path.exists(thumb_path):
        try:
            os.remove(thumb_path)
        except Exception as e:
            print(f"Could not delete temp thumb: {e}")

    return pdf_path