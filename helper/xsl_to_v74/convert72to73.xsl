<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv72to73">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv72to73"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>7.2</literal> to <literal>7.3</literal>.
</para>
<xsl:template match="image" mode="conv72to73">
    <xsl:choose>
        <!-- nothing to do if already at 7.3 -->
        <xsl:when test="@schemaversion > 7.2">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="7.3">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv72to73"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv72to73">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv72to73"/>
    </xsl:copy>
</xsl:template>

<!-- change vmx type to oem type with oem-resize set to false-->
<xsl:template match="type[@image='vmx']" mode="conv72to73">
    <type image="oem">
        <xsl:copy-of select="@*[local-name() != 'image']"/>
        <oemconfig>
            <xsl:apply-templates select="oemconfig/*[not(self::oem-resize)]" mode="conv72to73"/>
            <oem-resize>false</oem-resize>
        </oemconfig>
        <xsl:apply-templates select="*[not(self::oemconfig)]" mode="conv72to73"/>
    </type>
</xsl:template>

</xsl:stylesheet>
