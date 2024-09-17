<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes"
    omit-xml-declaration="no"
    encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="include">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="include"/>
    </xsl:copy>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="include">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="include"/>
    </xsl:copy>
</xsl:template>

<!-- incorporate optional include file(s) -->
<xsl:template match="image/include" mode="include">
    <xsl:param name="include_file_name" select="@from"/>
    <xsl:choose>
        <xsl:when test="document($include_file_name)">
            <xsl:copy-of select="document($include_file_name)/image/*"/>
            <xsl:apply-templates  mode="include"/>
        </xsl:when>
        <xsl:otherwise>
            <xsl:copy-of select="."/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

</xsl:stylesheet>
